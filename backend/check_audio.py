# C:\HEAI\backend\check_audio.py
import soundfile as sf
import numpy as np

path = r"C:\HEAI\backend\data\voice_samples\reference_clean.wav"
data, sr = sf.read(path)
print(f"Sample rate: {sr} Hz")
print(f"Channels: {1 if data.ndim == 1 else data.shape[1]}")
print(f"Duration: {len(data)/sr:.1f} saniye")
print(f"Max amplitude: {np.max(np.abs(data)):.3f}")
print(f"Shape: {data.shape}")