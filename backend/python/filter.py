import numpy as np
from scipy.signal import butter, sosfilt

# Guitar and piano frequency range
MIN_FREQ = 70    # Hz - below this is noise (low E string = 82Hz)
MAX_FREQ = 4200  # Hz - above this is electronic noise

SAMPLE_RATE = 48000

def butter_highpass(cutoff, fs, order=4):
    """Creates a High-Pass filter - removes frequencies that are too low"""
    nyq = fs / 2
    normal_cutoff = cutoff / nyq
    sos = butter(order, normal_cutoff, btype='high', output='sos')
    return sos

def butter_lowpass(cutoff, fs, order=4):
    """Creates a Low-Pass filter - removes frequencies that are too high"""
    nyq = fs / 2
    normal_cutoff = cutoff / nyq
    sos = butter(order, normal_cutoff, btype='low', output='sos')
    return sos

# Create filters once (not on every call)
highpass_sos = butter_highpass(MIN_FREQ, SAMPLE_RATE)
lowpass_sos  = butter_lowpass(MAX_FREQ, SAMPLE_RATE)

def filter_audio(audio_buffer):
    """
    Filters the audio - removes background noise
    Input:  numpy array of audio samples
    Output: clean numpy array
    """
    if len(audio_buffer) == 0:
        return audio_buffer

    # Step 1: Remove low frequencies (room noise, movement, rumble)
    filtered = sosfilt(highpass_sos, audio_buffer)

    # Step 2: Remove high frequencies (electronic noise, whistles)
    filtered = sosfilt(lowpass_sos, filtered)

    return filtered

def is_loud_enough(audio_buffer, threshold=0.01):
    """
    Checks if the sound is loud enough to analyze
    Prevents false detection during silence
    """
    rms = np.sqrt(np.mean(audio_buffer**2))
    return rms > threshold
