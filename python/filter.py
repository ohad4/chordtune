import numpy as np
from scipy.signal import butter, sosfilt

# טווח תדרים של גיטרה ופסנתר
MIN_FREQ = 70    # Hz - מתחת לזה רעש (מיתר E הנמוך = 82Hz)
MAX_FREQ = 4200  # Hz - מעל לזה רעש אלקטרוני

SAMPLE_RATE = 44100

def butter_highpass(cutoff, fs, order=4):
    """יצירת פילטר High-Pass - מסיר תדרים נמוכים מדי"""
    nyq = fs / 2
    normal_cutoff = cutoff / nyq
    sos = butter(order, normal_cutoff, btype='high', output='sos')
    return sos

def butter_lowpass(cutoff, fs, order=4):
    """יצירת פילטר Low-Pass - מסיר תדרים גבוהים מדי"""
    nyq = fs / 2
    normal_cutoff = cutoff / nyq
    sos = butter(order, normal_cutoff, btype='low', output='sos')
    return sos

# יצירת הפילטרים פעם אחת בלבד (לא בכל פעם)
highpass_sos = butter_highpass(MIN_FREQ, SAMPLE_RATE)
lowpass_sos  = butter_lowpass(MAX_FREQ, SAMPLE_RATE)

def filter_audio(audio_buffer):
    """
    סינון האודיו - מסיר רעשי רקע
    קלט:  מערך numpy של דגימות אודיו
    פלט:  מערך numpy נקי
    """
    if len(audio_buffer) == 0:
        return audio_buffer

    # שלב 1: הסרת תדרים נמוכים (רעשי חדר, תנועה, רחשים)
    filtered = sosfilt(highpass_sos, audio_buffer)

    # שלב 2: הסרת תדרים גבוהים (רעש אלקטרוני, שריקות)
    filtered = sosfilt(lowpass_sos, filtered)

    return filtered

def is_loud_enough(audio_buffer, threshold=0.01):
    """
    בדיקה אם הצליל חזק מספיק לניתוח
    מונע זיהוי שגוי כשיש שקט
    """
    rms = np.sqrt(np.mean(audio_buffer**2))
    return rms > threshold
