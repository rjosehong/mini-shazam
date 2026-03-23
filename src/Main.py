from src.database import SongDatabase
from src.recognize import record_and_recognize

db = SongDatabase()
db.index_directory("songs/")

audio, sr = load_audio("songs/rock_power.wav")
clip = audio[int(3 * sr):int(8 * sr)]  # 5-second clip
name, score, scores = recognize(clip, sr, db)

while True:
    input("press enter to start recognizing...")
    best_name, best_score, all_scores = record_and_recognize(db)

    print(f"Match: {best_name} (score: {best_score})")
    print(f"Hash table States: {db.table.stats()}")