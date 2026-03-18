"""
Generate synthetic WAV test songs for the Mini Shazam pipeline.

Each song is a unique mix of sine waves with varying frequencies,
amplitudes, and envelopes to simulate different "genres".
"""

import os
import wave
import struct
import numpy as np

SAMPLE_RATE = 22050
DURATION = 15  # seconds
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "songs")

SONGS = {
    "electronic_pulse": {
        "freqs": [220, 440, 660, 1100, 2200],
        "style": "pulse",
    },
    "acoustic_strum": {
        "freqs": [330, 392, 494, 587, 659],
        "style": "strum",
    },
    "classical_harmony": {
        "freqs": [262, 330, 392, 523, 659],
        "style": "sweep",
    },
    "rock_power": {
        "freqs": [147, 196, 294, 440, 880],
        "style": "distort",
    },
    "jazz_smooth": {
        "freqs": [277, 349, 415, 554, 698],
        "style": "vibrato",
    },
}


def generate_song(freqs, style, duration=DURATION, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    signal = np.zeros_like(t)

    for i, f in enumerate(freqs):
        amp = 1.0 / (i + 1)  # decreasing amplitude for harmonics
        if style == "pulse":
            # On/off pulse every 0.5s
            envelope = (np.sin(2 * np.pi * 2 * t) > 0).astype(float)
        elif style == "strum":
            # Exponential decay repeated
            period = duration / 4
            envelope = np.exp(-3 * (t % period) / period)
        elif style == "sweep":
            # Slowly sweeping frequency
            f = f * (1 + 0.1 * np.sin(2 * np.pi * 0.2 * t))
            envelope = np.ones_like(t)
        elif style == "distort":
            envelope = np.ones_like(t)
        elif style == "vibrato":
            f_mod = f * (1 + 0.02 * np.sin(2 * np.pi * 5 * t))
            phase = 2 * np.pi * np.cumsum(f_mod) / sr
            signal += amp * np.sin(phase)
            continue
        else:
            envelope = np.ones_like(t)

        signal += amp * envelope * np.sin(2 * np.pi * f * t)

    if style == "distort":
        signal = np.tanh(3 * signal)

    # Normalize
    signal = signal / (np.max(np.abs(signal)) + 1e-10) * 0.9
    return signal


def write_wav(filepath, audio, sr=SAMPLE_RATE):
    audio_int16 = (audio * 32767).astype(np.int16)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name, params in SONGS.items():
        audio = generate_song(params["freqs"], params["style"])
        path = os.path.join(OUTPUT_DIR, f"{name}.wav")
        write_wav(path, audio)
        print(f"Generated: {path} ({len(audio)/SAMPLE_RATE:.1f}s)")


if __name__ == "__main__":
    main()
