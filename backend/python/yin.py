import numpy as np

SAMPLE_RATE = 44100

# טווח תדרים לחיפוש
MIN_FREQ = 70    # Hz
MAX_FREQ = 1400  # Hz

# סף YIN - ככל שנמוך יותר, מדויק יותר אך רגיש יותר לרעש
YIN_THRESHOLD = 0.15

# שמות התווים
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def difference_function(audio_buffer, max_tau):
    """
    שלב 1: חישוב פונקציית ההבדלים
    משווה את האות לגרסה מוזזת שלו
    """
    n = len(audio_buffer)
    diff = np.zeros(max_tau)
    
    for tau in range(1, max_tau):
        diff[tau] = np.sum((audio_buffer[:n - tau] - audio_buffer[tau:n]) ** 2)
    
    return diff

def cumulative_mean_normalized(diff):
    """
    שלב 2: נרמול מצטבר (CMND)
    מנקה את הנתונים כדי שהדיפ האמיתי יהיה ברור
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
    שלב 3: מציאת הדיפ הראשון מתחת לסף
    זה אורך המחזור האמיתי של הגל
    """
    tau = 2
    while tau < len(cmnd) - 1:
        if cmnd[tau] < threshold:
            # מצא את המינימום המקומי
            while tau + 1 < len(cmnd) and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            return tau
        tau += 1
    
    # אם לא נמצא דיפ מתחת לסף - החזר את המינימום הכללי
    return np.argmin(cmnd[2:]) + 2

def parabolic_interpolation(cmnd, tau):
    """
    שיפור דיוק על ידי אינטרפולציה פרבולית
    נותן תדר מדויק יותר בין הדגימות
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
    פונקציה ראשית של YIN - זיהוי תדר
    קלט:  מערך numpy של אודיו מסונן
    פלט:  תדר בHz או None אם לא נמצא
    """
    min_tau = int(SAMPLE_RATE / MAX_FREQ)
    max_tau = int(SAMPLE_RATE / MIN_FREQ)
    max_tau = min(max_tau, len(audio_buffer) // 2)
    
    if max_tau <= min_tau:
        return None
    
    # שלב 1: פונקציית הבדלים
    diff = difference_function(audio_buffer, max_tau)
    
    # שלב 2: נרמול
    cmnd = cumulative_mean_normalized(diff)
    
    # שלב 3: מציאת הדיפ
    tau = find_first_dip(cmnd[min_tau:max_tau], YIN_THRESHOLD)
    tau += min_tau
    
    # שיפור דיוק
    tau_precise = parabolic_interpolation(cmnd, tau)
    
    if tau_precise <= 0:
        return None
    
    # שלב 4: חישוב תדר
    freq = SAMPLE_RATE / tau_precise
    
    if freq < MIN_FREQ or freq > MAX_FREQ:
        return None
    
    return freq

def freq_to_note(freq):
    """
    המרת תדר לתו מוזיקלי
    משתמש בנוסחת MIDI: N = 69 + 12 * log2(f / 440)
    """
    if freq <= 0:
        return None, None, 0
    
    # חישוב מספר MIDI
    midi = 69 + 12 * np.log2(freq / 440.0)
    midi_round = round(midi)
    
    # שם התו ואוקטבה
    note_index = midi_round % 12
    octave = (midi_round // 12) - 1
    note_name = NOTE_NAMES[note_index]
    
    # חישוב סטייה בסנטים
    cents = round((midi - midi_round) * 100)
    
    # בדיקה אם מכוון
    in_tune = abs(cents) <= 5
    
    return note_name, octave, cents, in_tune

def analyze(audio_buffer):
    """
    ניתוח מלא - קבלת אודיו והחזרת כל הנתונים
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
