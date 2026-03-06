import sounddevice as sd
import numpy as np
from flask import Flask, jsonify
from flask_cors import CORS
import threading
from collections import deque

from filter import filter_audio, is_loud_enough
from yin import analyze as analyze_pitch
from chord import analyze_chord

app = Flask(__name__)
CORS(app)

SAMPLE_RATE = 44100
BUFFER_SIZE = 4096

SMOOTHING_SIZE = 5
freq_history = deque(maxlen=SMOOTHING_SIZE)
chord_history = deque(maxlen=SMOOTHING_SIZE)

latest_data = {
    "tuner": { "note": None, "octave": None, "freq": 0, "cents": 0, "inTune": False },
    "chord": { "name": "--", "root": "--", "intervals": "--", "accuracy": 0 },
    "volume": 0,
    "listening": False,
    "micEnabled": True
}

audio_buffer = np.zeros(BUFFER_SIZE)
lock = threading.Lock()
mic_enabled = True

def smooth_freq(new_freq):
    if new_freq and new_freq > 0:
        freq_history.append(new_freq)
    if len(freq_history) == 0:
        return 0
    return float(np.median(list(freq_history)))

def smooth_chord(new_chord):
    if new_chord and new_chord != "--":
        chord_history.append(new_chord)
    if len(chord_history) == 0:
        return "--"
    return max(set(chord_history), key=list(chord_history).count)

def process_audio(buffer):
    global latest_data
    volume = float(np.sqrt(np.mean(buffer**2)))
    volume_db = min(100, round(volume * 500, 1))
    filtered = filter_audio(buffer)

    if not is_loud_enough(filtered):
        with lock:
            latest_data["volume"] = volume_db
            latest_data["listening"] = True
            latest_data["tuner"] = { "note": None, "octave": None, "freq": 0, "cents": 0, "inTune": False }
            latest_data["chord"] = { "name": "--", "root": "--", "intervals": "--", "accuracy": 0 }
        return

    tuner_result = analyze_pitch(filtered)
    smoothed_freq = smooth_freq(tuner_result.get("freq", 0))
    if smoothed_freq > 0:
        tuner_result["freq"] = round(smoothed_freq, 2)

    chord_result = analyze_chord(filtered)
    smoothed_chord_name = smooth_chord(chord_result.get("name", "--"))
    if smoothed_chord_name != "--":
        chord_result["name"] = smoothed_chord_name

    with lock:
        latest_data["tuner"] = tuner_result
        latest_data["chord"] = chord_result
        latest_data["volume"] = volume_db
        latest_data["listening"] = True

def audio_callback(indata, frames, time, status):
    global audio_buffer, mic_enabled
    if not mic_enabled:
        return
    audio_buffer = indata[:, 0].copy()
    threading.Thread(target=process_audio, args=(audio_buffer.copy(),), daemon=True).start()

def start_audio_stream():
    print("🎤 מיקרופון פעיל - מקשיב...")
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=BUFFER_SIZE,
        callback=audio_callback
    ):
        sd.sleep(-1)

@app.route("/data")
def get_data():
    with lock:
        return jsonify(latest_data)

@app.route("/mic/on", methods=["POST"])
def mic_on():
    global mic_enabled
    mic_enabled = True
    with lock:
        latest_data["micEnabled"] = True
        latest_data["listening"] = True
    return jsonify({"micEnabled": True})

@app.route("/mic/off", methods=["POST"])
def mic_off():
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
    return jsonify({"status": "ok", "listening": latest_data["listening"]})

if __name__ == "__main__":
    print("🚀 מפעיל ChordTune Python Server...")
    audio_thread = threading.Thread(target=start_audio_stream, daemon=True)
    audio_thread.start()
    print("🌐 שרת פועל על http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
