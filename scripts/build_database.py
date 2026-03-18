"""
Index all songs in songs/ and save the database to data/database.json.

Usage:
    python scripts/build_database.py
    python scripts/build_database.py /path/to/songs /path/to/output.json
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SongDatabase

SONGS_DIR = sys.argv[1] if len(sys.argv) > 1 else "songs"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "data/database.json"

db = SongDatabase()
db.index_directory(SONGS_DIR)
db.save(OUTPUT)
print(f"\nHash table stats: {db.table.stats()}")
