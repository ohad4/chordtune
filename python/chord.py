import numpy as np

SAMPLE_RATE = 44100

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# מאגר אקורדים מוכרים
# כל אקורד מוגדר על ידי קבוצת מרווחים (intervals) ביחס לתו הבסיס
CHORD_TEMPLATES = {
    "Major":      [0, 4, 7],
    "Minor":      [0, 3, 7],
    "7":          [0, 4, 7, 10],
    "maj7":       [0, 4, 7, 11],
    "m7":         [0, 3, 7, 10],
    "dim":        [0, 3, 6],
    "aug":        [0, 4, 8],
    "sus2":       [0, 2, 7],
    "sus4":       [0, 5, 7],
    "dim7":       [0, 3, 6, 9],
}

# מידע נוסף על כל אקורד להצגה ב-UI
CHORD_INFO = {
    "Major":  {"intervals": "1-3-5"},
    "Minor":  {"intervals": "1-b3-5"},
    "7":      {"intervals": "1-3-5-b7"},
    "maj7":   {"intervals": "1-3-5-7"},
    "m7":     {"intervals": "1-b3-5-b7"},
    "dim":    {"intervals": "1-b3-b5"},
    "aug":    {"intervals": "1-3-#5"},
    "sus2":   {"intervals": "1-2-5"},
    "sus4":   {"intervals": "1-4-5"},
    "dim7":   {"intervals": "1-b3-b5-bb7"},
}

def apply_hanning_window(audio_buffer):
    """
    שלב 1: החלת חלון Hanning
    מרכך את קצוות החלון למניעת תדרים מזויפים
    """
    window = np.hanning(len(audio_buffer))
    return audio_buffer * window

def compute_fft(audio_buffer):
    """
    שלב 2: חישוב FFT
    ממיר את האות מתחום הזמן לתחום התדר
    """
    windowed = apply_hanning_window(audio_buffer)
    fft_result = np.fft.rfft(windowed)
    magnitudes = np.abs(fft_result)
    
    # תדרים המתאימים לכל bin
    freqs = np.fft.rfftfreq(len(audio_buffer), d=1.0 / SAMPLE_RATE)
    
    return freqs, magnitudes

def find_peaks(freqs, magnitudes, min_freq=70, max_freq=1400, num_peaks=6):
    """
    שלב 3: מציאת פסגות (Peak Picking)
    מוצא את התדרים החזקים ביותר
    """
    # סינון לטווח תדרים רלוונטי
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    filtered_freqs = freqs[mask]
    filtered_mags = magnitudes[mask]
    
    if len(filtered_mags) == 0:
        return []
    
    # סף מינימלי - רק תדרים חזקים מספיק
    threshold = np.max(filtered_mags) * 0.15
    
    peaks = []
    for i in range(1, len(filtered_mags) - 1):
        if (filtered_mags[i] > filtered_mags[i-1] and
            filtered_mags[i] > filtered_mags[i+1] and
            filtered_mags[i] > threshold):
            peaks.append((filtered_freqs[i], filtered_mags[i]))
    
    # מיון לפי עוצמה ולקיחת החזקים ביותר
    peaks.sort(key=lambda x: x[1], reverse=True)
    return peaks[:num_peaks]

def freq_to_note_class(freq):
    """
    המרת תדר למחלקת תו (0-11)
    0=C, 1=C#, 2=D, ... 11=B
    """
    if freq <= 0:
        return None
    midi = 69 + 12 * np.log2(freq / 440.0)
    return int(round(midi)) % 12

def match_chord(note_classes):
    """
    שלב 4: התאמת אקורד
    משווה את קבוצת התווים למאגר האקורדים
    """
    if len(note_classes) < 2:
        return None, None, 0
    
    best_match = None
    best_root = None
    best_score = 0
    
    # ניסיון כל תו כתו בסיס אפשרי
    for root in range(12):
        # חישוב המרווחים ביחס לתו הבסיס
        intervals = set((n - root) % 12 for n in note_classes)
        
        # השוואה לכל תבנית אקורד
        for chord_type, template in CHORD_TEMPLATES.items():
            template_set = set(template)
            
            # חישוב ציון ההתאמה
            matches = len(intervals & template_set)
            total = len(template_set)
            score = matches / total
            
            # בונוס אם יש התאמה מדויקת
            if intervals == template_set:
                score += 0.5
            
            if score > best_score and matches >= 2:
                best_score = score
                best_match = chord_type
                best_root = root
    
    if best_match is None:
        return None, None, 0
    
    accuracy = min(99, int(best_score * 80))
    return NOTE_NAMES[best_root], best_match, accuracy

def analyze_chord(audio_buffer):
    """
    פונקציה ראשית - ניתוח אקורד מלא
    קלט:  מערך numpy של אודיו מסונן
    פלט:  מילון עם שם האקורד, root ומרווחים
    """
    # שלב 2: FFT
    freqs, magnitudes = compute_fft(audio_buffer)
    
    # שלב 3: מציאת פסגות
    peaks = find_peaks(freqs, magnitudes)
    
    if len(peaks) < 2:
        return {
            "name": "--",
            "root": "--",
            "intervals": "--",
            "accuracy": 0
        }
    
    # שלב 4: המרה לתווים
    note_classes = []
    for freq, mag in peaks:
        note = freq_to_note_class(freq)
        if note is not None and note not in note_classes:
            note_classes.append(note)
    
    # שלב 5: זיהוי אקורד
    root, chord_type, accuracy = match_chord(note_classes)
    
    if root is None:
        return {
            "name": "--",
            "root": "--",
            "intervals": "--",
            "accuracy": 0
        }
    
    chord_name = f"{root} {chord_type}" if chord_type != "Major" else root
    intervals = CHORD_INFO.get(chord_type, {}).get("intervals", "--")
    
    return {
        "name": chord_name,
        "root": root,
        "intervals": intervals,
        "accuracy": accuracy
    }
