"""
Record from the MacBook microphone, then play back the recording.

Usage:
    python scripts/test_audio.py          # default 5 seconds
    python scripts/test_audio.py 10       # record 10 seconds
"""

import sys

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 22050
DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 5

print(f"Recording {DURATION}s from microphone...")
audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
    device="MacBook Pro Microphone",
)
sd.wait()
audio = audio.flatten()
print(f"Recorded {len(audio)} samples (peak amplitude: {np.max(np.abs(audio)):.4f})")

print("Playing back...")
sd.play(audio, samplerate=SAMPLE_RATE, device="MacBook Pro Speakers")
sd.wait()
print("Done.")
