"""
Song database: wraps the custom hash table to index and store fingerprints.

Refer to GUIDE.md, Milestone 3 for detailed instructions.
"""

import json
import os

from src.fingerprint import fingerprint_audio
from src.hash_table import HashTable
from src.utils import load_audio


class SongDatabase:
    """
    Manages a library of indexed songs using YOUR custom HashTable.

    The database has two main data structures:
      - self.table: a HashTable mapping fingerprint hashes to (song_id, time_offset) pairs
      - self.song_names: a dict mapping song_id (int) to song name (str)

    You will implement:
      - index_song()      : Fingerprint a song and add it to the hash table
      - index_directory()  : Index all .wav files in a directory
      - save()             : Serialize the database to JSON
      - load()             : Deserialize a database from JSON (classmethod)
    """

    def __init__(self):
        self.table = HashTable()
        self.song_names = {}  # song_id -> song name
        self._next_id = 0

    def get_song_name(self, song_id):
        """Look up a song's name by its ID. Provided for you."""
        return self.song_names.get(song_id, f"Unknown (id={song_id})")

    # ------------------------------------------------------------------ #
    # Indexing — YOU IMPLEMENT THESE
    # ------------------------------------------------------------------ #

    def index_song(self, filepath, song_name=None):
        """
        Load an audio file, fingerprint it, and insert all fingerprints
        into the hash table.

        Steps:
          1. Load the audio file using load_audio(filepath) from utils.py
          2. Generate fingerprints using fingerprint_audio(audio, sr)
          3. Assign a song_id: use self._next_id, then increment it
          4. If song_name is None, derive it from the filename:
               os.path.splitext(os.path.basename(filepath))[0]
          5. Store the name: self.song_names[song_id] = song_name
          6. Insert every fingerprint into the hash table:
               for each (hash_val, time_offset) in fingerprints:
                   self.table.insert(hash_val, (song_id, time_offset))
          7. Print a status message (optional but helpful for debugging)
          8. Return the song_id

        Args:
            filepath: Path to a .wav file
            song_name: Optional display name (defaults to filename without extension)

        Returns:
            The assigned song_id (int)
        """
        # TODO: Implement index_song
        raise NotImplementedError("Implement index_song()")

    def index_directory(self, directory):
        """
        Index all .wav files in a directory.

        Steps:
          1. List all files in the directory that end with .wav (case-insensitive)
          2. Sort them alphabetically for deterministic ordering
          3. Call self.index_song() for each one
          4. Print summary stats (optional)

        Args:
            directory: Path to a directory containing .wav files
        """
        # TODO: Implement index_directory
        raise NotImplementedError("Implement index_directory()")

    # ------------------------------------------------------------------ #
    # Serialization — YOU IMPLEMENT THESE
    # ------------------------------------------------------------------ #

    def save(self, filepath):
        """
        Serialize the database to a JSON file.

        Why? Indexing songs takes time (FFT + fingerprinting). By saving
        the database to disk, you can index once and load instantly later.

        JSON format:
        {
            "song_names": {"0": "song_a", "1": "song_b", ...},
            "next_id": 3,
            "capacity": 10007,
            "entries": [[key, song_id, time_offset], ...]
        }

        Steps:
          1. Build the entries list by iterating over all buckets:
               for bucket in self.table._buckets:
                   for key, (song_id, time_offset) in bucket:
                       entries.append([int(key), int(song_id), int(time_offset)])
             IMPORTANT: Use int() to convert numpy integers to Python ints,
             otherwise json.dump() will fail!
          2. Build the data dict with song_names, next_id, capacity, entries
             Note: JSON keys must be strings, so convert song_id keys:
               {str(k): v for k, v in self.song_names.items()}
          3. Create the output directory if it doesn't exist
          4. Write JSON to file using json.dump()

        Args:
            filepath: Where to save the JSON file (e.g., "data/database.json")
        """
        # TODO: Implement save
        raise NotImplementedError("Implement save()")

    @classmethod
    def load(cls, filepath):
        """
        Load a database from a JSON file. This is a classmethod — it
        creates and returns a new SongDatabase instance.

        Steps:
          1. Read and parse the JSON file
          2. Create a new SongDatabase: db = cls()
          3. Restore song_names (convert string keys back to ints):
               db.song_names = {int(k): v for k, v in data["song_names"].items()}
          4. Restore _next_id from data
          5. Create a new HashTable with the saved capacity:
               db.table = HashTable(capacity=data["capacity"])
          6. Re-insert all entries:
               for key, song_id, time_offset in data["entries"]:
                   db.table.insert(key, (song_id, time_offset))
          7. Return db

        Args:
            filepath: Path to a saved JSON database

        Returns:
            A new SongDatabase instance with all data restored
        """
        # TODO: Implement load
        raise NotImplementedError("Implement load()")
