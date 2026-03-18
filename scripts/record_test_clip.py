"""
Record a 5-second test clip from the MacBook microphone and save it as a labeled WAV.

Usage:
    python scripts/record_test_clip.py "michael-jackson_billie-jean"

The filename encodes the expected song name:
    tests/clips/michael-jackson_billie-jean_001.wav

Run multiple times for the same song to build up test clips (auto-increments).
"""

import os
import sys
import wave
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 22050
DURATION = 5
CLIPS_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "clips")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/record_test_clip.py <song-name>")
        print()
        print("song-name must match the WAV filename in songs/ (without .wav)")
        print('Example: python scripts/record_test_clip.py "michael-jackson_billie-jean"')
        sys.exit(1)

    song_name = sys.argv[1]
    os.makedirs(CLIPS_DIR, exist_ok=True)

    # Find next clip number for this song
    existing = [
        f for f in os.listdir(CLIPS_DIR)
        if f.startswith(song_name + "_") and f.endswith(".wav")
    ]
    next_num = len(existing) + 1
    filename = f"{song_name}_{next_num:03d}.wav"
    filepath = os.path.join(CLIPS_DIR, filename)

    print(f"Play '{song_name}' near the mic, then press Enter to start recording...")
    input()

    print(f"Recording {DURATION}s...")
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device="MacBook Pro Microphone",
    )
    sd.wait()
    audio = audio.flatten()

    # Save as WAV
    audio_int16 = (audio * 32767).astype(np.int16)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())

    peak = np.max(np.abs(audio))
    print(f"Saved: {filepath} (peak amplitude: {peak:.4f})")


if __name__ == "__main__":
    main()
