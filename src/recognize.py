"""
Recognition module: fingerprint an audio clip and match it against the database.

Refer to GUIDE.md, Milestone 3 for detailed instructions.
"""

import numpy as np

from src.fingerprint import SAMPLE_RATE, fingerprint_audio
from src.utils import highpass_filter


def recognize(audio, sample_rate, database):
    """
    Fingerprint an audio clip and match it against the database.

    This is where the "second hash table" insight comes in: the offset
    histogram is conceptually another hash table mapping
    (time_delta -> count).

    Algorithm:
      1. Fingerprint the audio clip to get a list of (hash_value, t_clip)
      2. If no fingerprints, return (None, 0, {})
      3. For each fingerprint (hash_val, t_clip):
           - Look up hash_val in database.table to get all hits
           - Each hit is (song_id, t_song)
           - Compute delta = t_song - t_clip
           - Group deltas by song_id:
               matches[song_id].append(delta)
      4. If no matches, return (None, 0, {})
      5. For each song_id in matches:
           - Build an offset histogram: count how many times each delta appears
             (use a plain dict: {delta: count})
           - The peak count = max value in the histogram
           - Store: all_scores[song_name] = peak_count
           - Track the best song (highest peak_count)
      6. Return (best_song_name, best_score, all_scores)

    WHY does this work?
      If the clip is from song X starting at second 30, then every matching
      fingerprint will have roughly the same delta: (t_song - t_clip) will
      be ~constant. Random false matches from other songs will have random
      deltas that don't align. So the correct song gets a tall spike in
      its histogram while wrong songs get flat noise.

    Args:
        audio: 1D numpy array of audio samples
        sample_rate: sample rate of the audio
        database: a SongDatabase instance with indexed songs

    Returns:
        (best_song_name, best_score, all_scores)
        - best_song_name: name of the best matching song (or None)
        - best_score: peak histogram count for the best match
        - all_scores: dict {song_name: peak_histogram_count} for all candidates
    """
    # TODO: Implement the recognition algorithm
    #
    # Step 1: Fingerprint the clip
    #
    # Step 2: Collect all hash hits, grouped by song_id
    #   matches = {}  # song_id -> list of (t_song - t_clip)
    #   for hash_val, t_clip in fingerprints:
    #       hits = database.table.lookup(hash_val)
    #       for song_id, t_song in hits:
    #           delta = t_song - t_clip
    #           matches.setdefault(song_id, []).append(delta)
    #
    # Step 3: For each song, build offset histogram and find peak
    #   best_song_id = None
    #   best_count = 0
    #   all_scores = {}
    #   for song_id, deltas in matches.items():
    #       histogram = {}
    #       for d in deltas:
    #           histogram[d] = histogram.get(d, 0) + 1
    #       peak_count = max(histogram.values())
    #       song_name = database.get_song_name(song_id)
    #       all_scores[song_name] = peak_count
    #       if peak_count > best_count:
    #           best_count = peak_count
    #           best_song_id = song_id
    #
    # Step 4: Return results

    raise NotImplementedError("Implement recognize()")


def record_and_recognize(database, duration=5, sample_rate=SAMPLE_RATE):
    """
    Record from the microphone and identify the song.

    This function is provided for you — it handles the mic recording
    and calls your recognize() function.
    """
    import sounddevice as sd

    print(f"Recording {duration} seconds...")
    audio = sd.rec(
        int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float64"
    )
    sd.wait()
    audio = audio.flatten()
    # Remove low-frequency rumble from mic
    audio = highpass_filter(audio, cutoff=200, sample_rate=sample_rate)
    print("Recording complete. Matching...")

    best_name, best_score, all_scores = recognize(audio, sample_rate, database)

    if best_name:
        print(f"Match: {best_name} (score: {best_score})")
    else:
        print("No match found.")

    if all_scores:
        print("All scores:")
        for name, score in sorted(all_scores.items(), key=lambda x: -x[1]):
            print(f"  {name}: {score}")

    return best_name, best_score, all_scores
