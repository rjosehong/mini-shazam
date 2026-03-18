"""
Unit tests for YOUR fingerprinting implementation.

Run with:
    python -m pytest tests/student/test_fingerprint.py -v

These tests guide you through Milestone 2.
"""

import numpy as np
import pytest

from src.fingerprint import (
    SAMPLE_RATE,
    compute_spectrogram,
    find_peaks,
    fingerprint_audio,
    generate_fingerprints,
)


def _make_tone(freq=440, duration=3.0, sr=SAMPLE_RATE):
    """Generate a pure sine wave."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _make_chord(freqs=(440, 880, 1320), duration=3.0, sr=SAMPLE_RATE):
    """Generate a sum of sine waves."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return sum(np.sin(2 * np.pi * f * t) for f in freqs)


# ================================================================== #
# Spectrogram tests (compute_spectrogram is provided, these should pass)
# ================================================================== #


class TestSpectrogram:
    def test_shape(self):
        """Spectrogram should be a 2D matrix with matching axis arrays."""
        audio = _make_tone(duration=2.0)
        freqs, times, spec = compute_spectrogram(audio)
        assert spec.ndim == 2
        assert len(freqs) == spec.shape[0]
        assert len(times) == spec.shape[1]

    def test_dominant_frequency(self):
        """A 1000 Hz tone's spectrogram should peak near 1000 Hz."""
        audio = _make_tone(freq=1000, duration=2.0)
        freqs, times, spec = compute_spectrogram(audio)
        avg_spectrum = spec.mean(axis=1)
        peak_freq = freqs[np.argmax(avg_spectrum)]
        assert abs(peak_freq - 1000) < 50


# ================================================================== #
# Peak finding tests (YOU implement find_peaks)
# ================================================================== #


class TestPeakFinding:
    def test_finds_peaks(self):
        """find_peaks should return a non-empty list for a chord signal."""
        audio = _make_chord(duration=3.0)
        _, _, spec = compute_spectrogram(audio)
        peaks = find_peaks(spec)
        assert len(peaks) > 0

    def test_peaks_are_tuples(self):
        """Each peak should be a (time_bin, freq_bin) tuple."""
        audio = _make_tone(duration=2.0)
        _, _, spec = compute_spectrogram(audio)
        peaks = find_peaks(spec)
        for p in peaks:
            assert len(p) == 2  # (time_bin, freq_bin)


# ================================================================== #
# Fingerprint generation tests (YOU implement generate_fingerprints)
# ================================================================== #


class TestFingerprintGeneration:
    def test_generates_fingerprints(self):
        """fingerprint_audio should produce fingerprints for a chord signal."""
        audio = _make_chord(duration=3.0)
        fps = fingerprint_audio(audio)
        assert len(fps) > 0

    def test_fingerprint_structure(self):
        """Each fingerprint should be a (hash_value, time_offset) pair of ints."""
        audio = _make_chord(duration=3.0)
        fps = fingerprint_audio(audio)
        for h, t in fps:
            assert isinstance(h, (int, np.integer))
            assert isinstance(t, (int, np.integer))

    def test_different_signals_different_fingerprints(self):
        """Two different tones should produce mostly different fingerprint hashes."""
        audio1 = _make_tone(freq=440, duration=3.0)
        audio2 = _make_tone(freq=1500, duration=3.0)
        fps1 = set(h for h, _ in fingerprint_audio(audio1))
        fps2 = set(h for h, _ in fingerprint_audio(audio2))
        overlap = fps1 & fps2
        assert len(overlap) < 0.1 * max(len(fps1), len(fps2), 1)

    def test_same_signal_same_fingerprints(self):
        """The same signal should always produce the same fingerprints."""
        audio = _make_chord(duration=3.0)
        fps1 = fingerprint_audio(audio)
        fps2 = fingerprint_audio(audio)
        assert fps1 == fps2
