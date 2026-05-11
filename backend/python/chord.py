import numpy as np
import json
import os
import pickle

SAMPLE_RATE = 44100

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Load chord data from JSON
_json_path = os.path.join(os.path.dirname(__file__), "chords.json")
with open(_json_path, "r") as f:
    _chord_data = json.load(f)

CHORD_TEMPLATES = _chord_data["templates"]
CHORD_INFO      = _chord_data["info"]

# Load ML model if available
_model_path = os.path.join(os.path.dirname(__file__), "ml_model.pkl")
_ml_model = None
if os.path.exists(_model_path):
    with open(_model_path, "rb") as f:
        _ml_model = pickle.load(f)
    print("ML model loaded successfully")
else:
    print("ML model not found - using FFT only")

def apply_hanning_window(audio_buffer):
    """
    Step 1: Apply Hanning window
    Softens the edges of the buffer to prevent false frequencies
    """
    window = np.hanning(len(audio_buffer))
    return audio_buffer * window

def compute_fft(audio_buffer):
    """
    Step 2: Compute FFT
    Converts the signal from the time domain to the frequency domain
    """
    windowed = apply_hanning_window(audio_buffer)
    fft_result = np.fft.rfft(windowed)
    magnitudes = np.abs(fft_result)
    freqs = np.fft.rfftfreq(len(audio_buffer), d=1.0 / SAMPLE_RATE)
    return freqs, magnitudes

def find_peaks(freqs, magnitudes, min_freq=70, max_freq=1400, num_peaks=6):
    """
    Step 3: Peak Picking
    Finds the strongest frequencies
    """
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    filtered_freqs = freqs[mask]
    filtered_mags  = magnitudes[mask]

    if len(filtered_mags) == 0:
        return []

    threshold = np.max(filtered_mags) * 0.15

    peaks = []
    for i in range(1, len(filtered_mags) - 1):
        if (filtered_mags[i] > filtered_mags[i-1] and
            filtered_mags[i] > filtered_mags[i+1] and
            filtered_mags[i] > threshold):
            peaks.append((filtered_freqs[i], filtered_mags[i]))

    peaks.sort(key=lambda x: x[1], reverse=True)
    return peaks[:num_peaks]

def freq_to_note_class(freq):
    """
    Converts frequency to note class (0-11)
    0=C, 1=C#, 2=D, ... 11=B
    """
    if freq <= 0:
        return None
    midi = 69 + 12 * np.log2(freq / 440.0)
    return int(round(midi)) % 12

def note_classes_to_feature_vector(note_classes):
    """
    Converts note classes to a 24-value feature vector:
    - First 12: which notes are present
    - Last 12:  estimated root note (lowest detected note)
    """
    # First 12 - notes present
    notes = [0.0] * 12
    for note in note_classes:
        notes[note % 12] = 1.0

    # Last 12 - root note (first detected note = likely the root)
    root_vec = [0.0] * 12
    if note_classes:
        root_vec[note_classes[0] % 12] = 1.0

    return notes + root_vec

def predict_with_ml(note_classes):
    """
    Chord recognition using ML model
    """
    if _ml_model is None or len(note_classes) < 2:
        return None, None, 0

    features = note_classes_to_feature_vector(note_classes)
    prediction = _ml_model.predict([features])[0]
    probabilities = _ml_model.predict_proba([features])[0]
    confidence = int(max(probabilities) * 100)

    parts = prediction.split("_", 1)
    if len(parts) != 2:
        return None, None, 0

    root, chord_type = parts
    return root, chord_type, confidence

def match_chord(note_classes):
    """
    Chord recognition using template matching (fallback)
    """
    if len(note_classes) < 2:
        return None, None, 0

    best_match = None
    best_root  = None
    best_score = 0

    for root in range(12):
        intervals = set((n - root) % 12 for n in note_classes)

        for chord_type, template in CHORD_TEMPLATES.items():
            template_set = set(template)
            matches = len(intervals & template_set)
            total   = len(template_set)
            score   = matches / total

            if intervals == template_set:
                score += 0.5

            if score > best_score and matches >= 2:
                best_score = score
                best_match = chord_type
                best_root  = root

    if best_match is None:
        return None, None, 0

    accuracy = min(99, int(best_score * 80))
    return NOTE_NAMES[best_root], best_match, accuracy

def analyze_chord(audio_buffer):
    """
    Main function - full chord analysis
    Uses ML if model exists, otherwise falls back to FFT template matching
    """
    freqs, magnitudes = compute_fft(audio_buffer)
    peaks = find_peaks(freqs, magnitudes)

    if len(peaks) < 2:
        return {"name": "--", "root": "--", "intervals": "--", "accuracy": 0}

    note_classes = []
    for freq, mag in peaks:
        note = freq_to_note_class(freq)
        if note is not None and note not in note_classes:
            note_classes.append(note)

    if _ml_model is not None:
        root, chord_type, accuracy = predict_with_ml(note_classes)
    else:
        root, chord_type, accuracy = match_chord(note_classes)

    if root is None:
        return {"name": "--", "root": "--", "intervals": "--", "accuracy": 0}

    chord_name = f"{root} {chord_type}" if chord_type != "Major" else root
    intervals  = CHORD_INFO.get(chord_type, {}).get("intervals", "--")

    return {
        "name":      chord_name,
        "root":      root,
        "intervals": intervals,
        "accuracy":  accuracy
    }
