import numpy as np

SAMPLE_RATE = 48000

# Frequency search range
MIN_FREQ = 70    # Hz
MAX_FREQ = 1400  # Hz

# YIN threshold - lower = more accurate but more sensitive to noise
YIN_THRESHOLD = 0.15

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def difference_function(audio_buffer, max_tau):
    """
    Step 1: Compute difference function
    Compares the signal to a shifted version of itself
    """
    n = len(audio_buffer)
    diff = np.zeros(max_tau)

    for tau in range(1, max_tau):
        diff[tau] = np.sum((audio_buffer[:n - tau] - audio_buffer[tau:n]) ** 2)

    return diff

def cumulative_mean_normalized(diff):
    """
    Step 2: Cumulative Mean Normalized Difference (CMND)
    Normalizes the data so the true dip is clear
    """
    cmnd = np.zeros(len(diff))
    cmnd[0] = 1

    cumsum = 0
    for tau in range(1, len(diff)):
        cumsum += diff[tau]
        if cumsum == 0:
            cmnd[tau] = 1
        else:
            cmnd[tau] = diff[tau] * tau / cumsum

    return cmnd

def find_first_dip(cmnd, threshold):
    """
    Step 3: Find the first dip below the threshold
    This is the true period of the wave
    """
    tau = 2
    while tau < len(cmnd) - 1:
        if cmnd[tau] < threshold:
            while tau + 1 < len(cmnd) and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            return tau
        tau += 1

    # If no dip found below threshold - return the global minimum
    return np.argmin(cmnd[2:]) + 2

def parabolic_interpolation(cmnd, tau):
    """
    Improves accuracy using parabolic interpolation
    Gives a more precise frequency between samples
    """
    if tau <= 0 or tau >= len(cmnd) - 1:
        return float(tau)

    s0, s1, s2 = cmnd[tau - 1], cmnd[tau], cmnd[tau + 1]
    denom = s0 - 2 * s1 + s2

    if denom == 0:
        return float(tau)

    return tau - (s2 - s0) / (2 * denom)

def detect_pitch(audio_buffer):
    """
    Main YIN function - pitch detection
    Input:  filtered numpy audio array
    Output: frequency in Hz or None if not found
    """
    min_tau = int(SAMPLE_RATE / MAX_FREQ)
    max_tau = int(SAMPLE_RATE / MIN_FREQ)
    max_tau = min(max_tau, len(audio_buffer) // 2)

    if max_tau <= min_tau:
        return None

    # Step 1: Difference function
    diff = difference_function(audio_buffer, max_tau)

    # Step 2: Normalize
    cmnd = cumulative_mean_normalized(diff)

    # Step 3: Find the dip
    tau = find_first_dip(cmnd[min_tau:max_tau], YIN_THRESHOLD)
    tau += min_tau

    # Improve accuracy
    tau_precise = parabolic_interpolation(cmnd, tau)

    if tau_precise <= 0:
        return None

    # Step 4: Calculate frequency
    freq = SAMPLE_RATE / tau_precise

    if freq < MIN_FREQ or freq > MAX_FREQ:
        return None

    return freq

def freq_to_note(freq):
    """
    Converts frequency to musical note
    Uses MIDI formula: N = 69 + 12 * log2(f / 440)
    """
    if freq <= 0:
        return None, None, 0

    midi = 69 + 12 * np.log2(freq / 440.0)
    midi_round = round(midi)

    note_index = midi_round % 12
    octave = (midi_round // 12) - 1
    note_name = NOTE_NAMES[note_index]

    cents = round((midi - midi_round) * 100)
    in_tune = abs(cents) <= 5

    return note_name, octave, cents, in_tune

def analyze(audio_buffer):
    """
    Full analysis - receives audio and returns all data
    """
    freq = detect_pitch(audio_buffer)

    if freq is None:
        return {
            "note": None,
            "octave": None,
            "freq": 0,
            "cents": 0,
            "inTune": False
        }

    note, octave, cents, in_tune = freq_to_note(freq)

    return {
        "note": note,
        "octave": octave,
        "freq": round(freq, 2),
        "cents": int(cents),
        "inTune": bool(in_tune)
    }
