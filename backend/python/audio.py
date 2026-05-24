import sounddevice as sd
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
from collections import deque

from filter import filter_audio, is_loud_enough
from yin import analyze as analyze_pitch
from chord import analyze_chord

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────
# Constants
# ─────────────────────────────────────────
SAMPLE_RATE = 48000       # 44,100 samples per second (CD standard)
BUFFER_SIZE = 4096        # samples per chunk (~93ms per buffer)

SMOOTHING_SIZE = 5       # number of buffers used for smoothing (improves stability) - UPDATED TO 5
freq_history = deque(maxlen=SMOOTHING_SIZE)
chord_history = deque(maxlen=SMOOTHING_SIZE)

# Number of silent buffers before resetting the display (~1.5 seconds)
# 16 buffers × 93ms = ~1.49 seconds
SILENCE_THRESHOLD = 5
silence_counter = 0

# ─────────────────────────────────────────
# Shared state (read by Flask, written by audio thread)
# ─────────────────────────────────────────
latest_data = {
    "tuner": { "note": None, "octave": None, "freq": 0, "cents": 0, "inTune": False },
    "chord": { "name": "--", "root": "--", "intervals": "--", "accuracy": 0 },
    "volume": 0,
    "listening": False,
    "micEnabled": True
}

audio_buffer = np.zeros(BUFFER_SIZE)
lock = threading.Lock()       # prevents race conditions between threads
mic_enabled = True
current_device = None

# ─────────────────────────────────────────
# Device filtering
# ─────────────────────────────────────────
EXCLUDE_KEYWORDS = [
    "mapper", "primary", "stereo mix", "what u hear",
    "wave out", "loopback", "virtual", "output", "line in",
    "sonar", "voicemeeter", "cable"
]

def get_input_devices():
    """Returns only real microphones - no duplicates, prefers the cleanest name"""
    import re

    EXCLUDE = [
        "mapper", "primary sound", "stereo mix", "line in",
        "sonar", "voicemeeter", "cable", "wave out", "loopback"
    ]

    candidates = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] == 0:
            continue
        name = d["name"].strip()
        if any(kw in name.lower() for kw in EXCLUDE):
            continue

        brand_match = re.search(r'\(([^)]+)\)', name)
        if brand_match:
            brand = brand_match.group(1).strip()
            brand = re.sub(r'^\d+[-\s]+', '', brand).strip()
        else:
            brand = name

        candidates.append({"index": i, "name": brand})

    # Remove duplicates — keep one per brand
    groups = {}
    for c in candidates:
        key = c["name"].lower().split()[0] if c["name"].split() else c["name"].lower()
        groups[key] = c

    return list(groups.values())

# ─────────────────────────────────────────
# Smoothing functions
# ─────────────────────────────────────────
def smooth_freq(new_freq):
    """
    Smooths the frequency using a rolling median.
    Prevents the display from jumping between values.
    """
    if new_freq and new_freq > 0:
        freq_history.append(new_freq)
    if len(freq_history) == 0:
        return 0
    return float(np.median(list(freq_history)))

def smooth_chord(new_chord):
    """
    Smooths the chord name using majority voting.
    Returns the most common chord in the last SMOOTHING_SIZE buffers.
    """
    if new_chord and new_chord != "--":
        chord_history.append(new_chord)
    if len(chord_history) == 0:
        return "--"
    return max(set(chord_history), key=list(chord_history).count)

# ─────────────────────────────────────────
# Main audio processing
# ─────────────────────────────────────────
def process_audio(buffer):
    """
    Called for every audio buffer (~93ms).
    Pipeline: filter → pitch detection (YIN) → chord detection (FFT + ML) → smooth → store
    """
    global latest_data, silence_counter

    # Calculate volume (RMS)
    volume = float(np.sqrt(np.mean(buffer**2)))
    volume_db = min(100, round(volume * 500, 1))

    # Apply Butterworth band-pass filter (70Hz - 4200Hz)
    filtered = filter_audio(buffer)

    # If signal is too quiet — increment silence counter
    if not is_loud_enough(filtered):
        silence_counter += 1

        # Only reset display after SILENCE_THRESHOLD silent buffers (~1.5 seconds)
        if silence_counter >= SILENCE_THRESHOLD:
            with lock:
                latest_data["volume"] = volume_db
                latest_data["listening"] = True
                latest_data["tuner"] = { "note": None, "octave": None, "freq": 0, "cents": 0, "inTune": False }
                latest_data["chord"] = { "name": "--", "root": "--", "intervals": "--", "accuracy": 0 }
        else:
            # Still within silence window — keep last result, only update volume
            with lock:
                latest_data["volume"] = volume_db
        return

    # Sound detected — reset silence counter
    silence_counter = 0

    # Step 1: Pitch detection using YIN algorithm
    tuner_result = analyze_pitch(filtered)
    smoothed_freq = smooth_freq(tuner_result.get("freq", 0))
    if smoothed_freq > 0:
        tuner_result["freq"] = round(smoothed_freq, 2)

    # Step 2: Chord detection using FFT + Random Forest
    chord_result = analyze_chord(filtered)
    smoothed_chord_name = smooth_chord(chord_result.get("name", "--"))
    if smoothed_chord_name != "--":
        chord_result["name"] = smoothed_chord_name

    # Step 3: Store results (thread-safe)
    with lock:
        latest_data["tuner"] = tuner_result
        latest_data["chord"] = chord_result
        latest_data["volume"] = volume_db
        latest_data["listening"] = True

# ─────────────────────────────────────────
# Audio stream
# ─────────────────────────────────────────
def audio_callback(indata, frames, time, status):
    """
    Called by sounddevice for every buffer.
    Spawns a new thread for processing to avoid blocking audio capture.
    """
    global audio_buffer, mic_enabled
    if not mic_enabled:
        return
    audio_buffer = indata[:, 0].copy()
    threading.Thread(target=process_audio, args=(audio_buffer.copy(),), daemon=True).start()

def start_audio_stream(device=None):
    """Opens the microphone input stream and keeps it running."""
    print(f"Starting microphone... (device={device})")
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=BUFFER_SIZE,
            device=device,
            callback=audio_callback
        ):
            sd.sleep(-1)
    except Exception as e:
        print(f"Microphone error: {e}")

# ─────────────────────────────────────────
# Flask API routes
# ─────────────────────────────────────────
@app.route("/data")
def get_data():
    """Returns all current data (tuner, chord, volume, listening state)."""
    with lock:
        return jsonify(latest_data)

@app.route("/devices")
def get_devices():
    """Returns list of available microphones."""
    devices = get_input_devices()
    return jsonify({ "devices": devices, "current": current_device })

@app.route("/devices/select", methods=["POST"])
def select_device():
    """Switches to a new microphone device."""
    global current_device
    data = request.get_json()
    new_device = data.get("index")
    current_device = new_device
    freq_history.clear()
    chord_history.clear()
    threading.Thread(target=start_audio_stream, args=(new_device,), daemon=True).start()
    return jsonify({ "success": True, "device": new_device })

@app.route("/mic/on", methods=["POST"])
def mic_on():
    """Enables the microphone."""
    global mic_enabled
    mic_enabled = True
    with lock:
        latest_data["micEnabled"] = True
        latest_data["listening"] = True
    return jsonify({"micEnabled": True})

@app.route("/mic/off", methods=["POST"])
def mic_off():
    """Disables the microphone and clears all history."""
    global mic_enabled
    mic_enabled = False
    freq_history.clear()
    chord_history.clear()
    with lock:
        latest_data["micEnabled"] = False
        latest_data["listening"] = False
        latest_data["volume"] = 0
        latest_data["tuner"] = { "note": None, "octave": None, "freq": 0, "cents": 0, "inTune": False }
        latest_data["chord"] = { "name": "--", "root": "--", "intervals": "--", "accuracy": 0 }
    return jsonify({"micEnabled": False})

@app.route("/status")
def get_status():
    """Health check endpoint."""
    return jsonify({"status": "ok", "listening": latest_data["listening"]})

# ─────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("Starting ChordTune Python Server...")
    audio_thread = threading.Thread(target=start_audio_stream, args=(current_device,), daemon=True)
    audio_thread.start()
    print("Server running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
