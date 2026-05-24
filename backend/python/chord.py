import numpy as np
import json
import os
import pickle

# Audio sample rate (48,000 samples per second - high quality standard)
SAMPLE_RATE = 48000

# List of musical note names (chromatic order)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# ---------------------------------------------------------
# Load chord data from JSON file
# ---------------------------------------------------------
_json_path = os.path.join(os.path.dirname(__file__), "chords.json")
with open(_json_path, "r") as f:
    _chord_data = json.load(f)

# Interval templates for each chord (e.g., Major is [0, 4, 7])
CHORD_TEMPLATES = _chord_data["templates"]
# Textual info for display (like "1-3-5")
CHORD_INFO      = _chord_data["info"]

# ---------------------------------------------------------
# Load the Machine Learning model (Random Forest)
# ---------------------------------------------------------
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
    Applies a Hanning window to the audio buffer.
    This mathematical process smooths the edges of the audio sample to zero,
    preventing 'Spectral Leakage' during the FFT.
    """
    window = np.hanning(len(audio_buffer))
    return audio_buffer * window


def compute_fft(audio_buffer):
    """
    Computes the Fast Fourier Transform (FFT) to convert the audio signal from time to frequency domain.
    Uses Zero-Padding to significantly increase frequency resolution, which is critical for detecting low notes (bass).
    """
    windowed = apply_hanning_window(audio_buffer)
    # Pad the array with zeros to increase resolution by 4x
    padded = np.pad(windowed, (0, len(windowed) * 3))
    fft_result = np.fft.rfft(padded)
    magnitudes = np.abs(fft_result) # Magnitude of the frequency
    freqs = np.fft.rfftfreq(len(padded), d=1.0 / SAMPLE_RATE) # The frequency itself
    return freqs, magnitudes


def find_peaks(freqs, magnitudes, min_freq=70, max_freq=1400, num_peaks=15):
    """
    Finds the strongest frequencies (Peaks) from the FFT within the relevant guitar range.
    Returns the top 15 frequencies to ensure we don't miss weak notes in the chord.
    """
    # Filter frequencies only for our target range (70Hz - 1400Hz)
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    filtered_freqs = freqs[mask]
    filtered_mags  = magnitudes[mask]

    if len(filtered_mags) == 0:
        return []

    # Minimum threshold: frequency must be at least 15% of the max magnitude in range
    threshold = np.max(filtered_mags) * 0.15

    peaks = []
    # Search for local "peaks"
    for i in range(1, len(filtered_mags) - 1):
        if (filtered_mags[i] > filtered_mags[i-1] and
            filtered_mags[i] > filtered_mags[i+1] and
            filtered_mags[i] > threshold):
            peaks.append((filtered_freqs[i], filtered_mags[i]))

    # Sort from strongest to weakest and take the top 15
    peaks.sort(key=lambda x: x[1], reverse=True)
    return peaks[:num_peaks]


def freq_to_note_class(freq):
    """
    Converts frequency (Hz) to a representative musical note class (0 to 11).
    Uses the standard formula based on A4 = 440Hz.
    Example: returns 0 for C, 1 for C#, etc.
    """
    if freq <= 0:
        return None
    midi = 69 + 12 * np.log2(freq / 440.0)
    return int(round(midi)) % 12


def note_classes_to_feature_vector(note_classes_with_mags, peaks_with_freqs):
    """
    Prepares the data format for the ML model (a 24-value vector).
    - First 12 values: normalized magnitude (0 to 1) for each of the 12 notes.
    - Next 12 values: One-hot representation of the "Root note" (lowest detected frequency marked as 1).
    """
    notes = [0.0] * 12

    if not note_classes_with_mags:
        return notes + [0.0] * 12

    # Normalize magnitudes so the strongest note gets a value of 1.0
    max_mag = max(mag for _, mag in note_classes_with_mags)
    if max_mag == 0:
        max_mag = 1.0

    for note, mag in note_classes_with_mags:
        note_class = note % 12
        normalized = mag / max_mag
        # Keep only the highest magnitude for each note (if it appeared in multiple octaves)
        if normalized > notes[note_class]:
            notes[note_class] = normalized

    # Identify the Root Note - based on the lowest frequency in the filtered peaks
    root_vec = [0.0] * 12
    if peaks_with_freqs:
        lowest_freq_peak = min(peaks_with_freqs, key=lambda x: x[0])
        lowest_note_class = freq_to_note_class(lowest_freq_peak[0])
        if lowest_note_class is not None:
            root_vec[lowest_note_class] = 1.0

    return notes + root_vec


def predict_with_ml(note_classes_with_mags, peaks_with_freqs):
    """
    Runs the Random Forest ML model to identify the chord.
    Returns the chord root, chord type, and confidence level.
    """
    if _ml_model is None or len(note_classes_with_mags) < 2:
        return None, None, 0

    features = note_classes_to_feature_vector(note_classes_with_mags, peaks_with_freqs)
    prediction = _ml_model.predict([features])[0]
    probabilities = _ml_model.predict_proba([features])[0]
    confidence = int(max(probabilities) * 100)

    # The model returns a string like "C_Major", so we split it
    parts = prediction.split("_", 1)
    if len(parts) != 2:
        return None, None, 0

    root, chord_type = parts
    return root, chord_type, confidence


def match_chord_simple(note_classes_with_mags):
    """
    Fallback mechanism based on simple interval matching.
    Triggered if the model found nothing, or if the model found an overly 
    complex chord that we prefer to verify against basic templates (Major, Minor, 7) first.
    """
    note_classes = [note for note, _ in note_classes_with_mags]

    if len(note_classes) < 2:
        return None, None, 0

    simple_types = ["Major", "Minor", "7", "maj7", "m7"]

    best_match = None
    best_root  = None
    best_score = 0

    # Iterate over all 12 possible notes as the root
    for root in range(12):
        intervals = set((n - root) % 12 for n in note_classes)

        # Check for matches against simple chord templates
        for chord_type in simple_types:
            template = CHORD_TEMPLATES[chord_type]
            template_set = set(template)
            matches = len(intervals & template_set)
            total   = len(template_set)
            score   = matches / total

            # Bonus for a perfect match (no missing or extra notes)
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
    Main function for chord analysis.
    Workflow:
    1. Compute FFT and find peaks.
    2. Apply Noise Gate to filter out natural harmonics (prevents Major/maj7 confusion).
    3. Attempt ML model recognition (Random Forest).
    4. Fallback to template matching if needed.
    """
    freqs, magnitudes = compute_fft(audio_buffer)
    peaks = find_peaks(freqs, magnitudes)

    if len(peaks) < 2:
        return {"name": "--", "root": "--", "intervals": "--", "accuracy": 0}

    # Build initial list of notes and magnitudes (before noise filtering)
    temp_notes = []
    seen_notes = set()
    for freq, mag in peaks:
        note = freq_to_note_class(freq)
        if note is not None and note not in seen_notes:
            temp_notes.append((note, mag))
            seen_notes.add(note)

    if not temp_notes:
        return {"name": "--", "root": "--", "intervals": "--", "accuracy": 0}

    # --- THE FIX: NOISE GATE ---
    # Filters out any note whose magnitude is less than 35% of the strongest note.
    # This prevents the app from picking up weak echo frequencies and mistaking a 
    # regular chord for a 7th chord (e.g., D maj7 instead of D).
    max_mag = max(mag for _, mag in temp_notes)
    threshold = max_mag * 0.35
    
    note_classes_with_mags = [(n, m) for n, m in temp_notes if m >= threshold]
    
    # Also filter the original peaks list so the root note detector doesn't accidentally pick up low background noise
    filtered_note_classes = set(n for n, _ in note_classes_with_mags)
    filtered_peaks = [p for p in peaks if freq_to_note_class(p[0]) in filtered_note_classes]

    if len(note_classes_with_mags) < 2:
        return {"name": "--", "root": "--", "intervals": "--", "accuracy": 0}

    root = None
    chord_type = None
    accuracy = 0

    simple_types = ["Major", "Minor", "7", "maj7", "m7"]

    # Step 1: Attempt ML recognition
    if _ml_model is not None:
        root, chord_type, accuracy = predict_with_ml(note_classes_with_mags, filtered_peaks)

        # If ML returned a complex chord (sus, dim, aug), verify with the simple fallback to prevent false positives
        if chord_type is not None and chord_type not in simple_types:
            root, chord_type, accuracy = match_chord_simple(note_classes_with_mags)

    # If no ML model, use only the fallback mechanism
    else:
        root, chord_type, accuracy = match_chord_simple(note_classes_with_mags)

    # If no valid recognition was found
    if root is None or chord_type is None:
        return {"name": "--", "root": "--", "intervals": "--", "accuracy": 0}

    # Construct the final chord name (e.g.: if C Major, show C. If C Minor, show C Minor)
    chord_name = f"{root} {chord_type}" if chord_type != "Major" else root
    intervals  = CHORD_INFO.get(chord_type, {}).get("intervals", "--")

    return {
        "name":      chord_name,
        "root":      root,
        "intervals": intervals,
        "accuracy":  accuracy
    }