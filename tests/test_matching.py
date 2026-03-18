"""
Integration tests for the full recognition pipeline.

Run with:
    python -m pytest tests/student/test_matching.py -v

These tests guide you through Milestone 3.
They build a small database of synthetic songs and test recognition.
"""

import numpy as np
import pytest

from src.database import SongDatabase
from src.fingerprint import SAMPLE_RATE, fingerprint_audio
from src.hash_table import HashTable
from src.recognize import recognize


def _make_song(freqs, duration=5.0, sr=SAMPLE_RATE):
    """
    Create a synthetic 'song' with harmonics and time variation.

    Each frequency gets 3 harmonics with amplitude modulation,
    making the signal spectrally rich enough for robust fingerprinting.
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    signal = np.zeros_like(t)
    for i, f in enumerate(freqs):
        for harmonic in range(1, 4):
            mod = 1.0 + 0.5 * np.sin(2 * np.pi * (0.5 + i * 0.3) * t)
            signal += mod * np.sin(2 * np.pi * f * harmonic * t) / harmonic
    return signal


class TestRecognition:
    @pytest.fixture
    def db_with_songs(self):
        """Build a database with 3 synthetic songs."""
        db = SongDatabase()
        songs = {
            "song_a": [200, 500, 1200],
            "song_b": [300, 700, 1500, 2000],
            "song_c": [400, 900, 1800],
        }
        for name, freqs in songs.items():
            audio = _make_song(freqs, duration=10.0)
            fps = fingerprint_audio(audio)
            song_id = db._next_id
            db._next_id += 1
            db.song_names[song_id] = name
            for h, t in fps:
                db.table.insert(h, (song_id, t))
        return db

    def test_exact_match(self, db_with_songs):
        """A full-length song should match itself with a high score."""
        audio = _make_song([300, 700, 1500, 2000], duration=10.0)
        name, score, _ = recognize(audio, SAMPLE_RATE, db_with_songs)
        assert name == "song_b"
        assert score > 5

    def test_clip_match(self, db_with_songs):
        """A 5-second clip from the middle of a song should still match."""
        full = _make_song([400, 900, 1800], duration=10.0)
        start = int(2.0 * SAMPLE_RATE)
        end = int(7.0 * SAMPLE_RATE)
        clip = full[start:end]
        name, score, _ = recognize(clip, SAMPLE_RATE, db_with_songs)
        assert name == "song_c"

    def test_no_match_for_unknown(self, db_with_songs):
        """A signal not in the database should score low."""
        unknown = _make_song([150, 3500, 4500], duration=5.0)
        name, score, _ = recognize(unknown, SAMPLE_RATE, db_with_songs)
        if name is not None:
            assert score < 50

    def test_noisy_clip(self, db_with_songs):
        """Recognition should still work with 10% noise added."""
        audio = _make_song([200, 500, 1200], duration=10.0)
        np.random.seed(42)
        noisy = audio + 0.1 * np.random.randn(len(audio))
        name, score, _ = recognize(noisy, SAMPLE_RATE, db_with_songs)
        assert name == "song_a"

    def test_all_scores_returned(self, db_with_songs):
        """The all_scores dict should contain the winning song with the highest score."""
        audio = _make_song([300, 700, 1500, 2000], duration=10.0)
        _, _, all_scores = recognize(audio, SAMPLE_RATE, db_with_songs)
        assert "song_b" in all_scores
        assert all_scores["song_b"] == max(all_scores.values())
