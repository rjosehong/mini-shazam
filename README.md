# Mini Shazam — Student Implementation Guide

Build a simplified version of Shazam that can identify songs from short audio clips recorded through your computer's microphone. Along the way you'll implement a hash table from scratch, learn about audio fingerprinting, and see how data structures power real-world applications.

**What you'll build:**

```
"What song is this?" ──► Microphone ──► Fingerprinting ──► Hash Table Lookup ──► "It's Billie Jean!"
```

**What you'll learn:**
- Hash tables with separate chaining — the core data structure
- Hash function design and collision analysis
- Audio fingerprinting (the Shazam algorithm)
- How hash tables enable O(1) lookup at massive scale

---

## Table of Contents

1. [How Shazam Works — The Big Picture](#1-how-shazam-works--the-big-picture)
2. [Setup](#2-setup)
3. [Milestone 1: The Hash Table](#3-milestone-1-the-hash-table)
4. [Milestone 2: Audio Fingerprinting](#4-milestone-2-audio-fingerprinting)
5. [Milestone 3: Indexing and Matching](#5-milestone-3-indexing-and-matching)
6. [Milestone 4: Live Recognition](#6-milestone-4-live-recognition)
7. [Discussion Questions](#7-discussion-questions)
8. [Reference](#8-reference)

---

## 1. How Shazam Works — The Big Picture

Shazam was published in 2003 by Avery Wang in the paper *"An Industrial-Strength Audio Search Algorithm."* The core insight is surprisingly simple:

> **A song can be identified by the pattern of its loudest frequencies over time.**

The system has two phases:

### Phase 1: Indexing (done once)

For every song in the library:

1. Convert the audio into a **spectrogram** — a 2D map of frequency vs. time
2. Find the **peaks** — the loudest points in the spectrogram (the "constellation")
3. Pair nearby peaks into **fingerprints** — each fingerprint encodes "frequency A at time T₁, frequency B at time T₂"
4. Store each fingerprint in a **hash table**: `hash(fingerprint) → (song_id, time_position)`

### Phase 2: Recognition (done each time you "Shazam" a song)

1. Record a short clip (5 seconds)
2. Run the same fingerprinting pipeline on the clip
3. Look up each fingerprint hash in the hash table
4. The trick: a true match will have **time-coherent** hits — the time offset between the database position and the clip position will be roughly constant for all matching fingerprints
5. Count these coherent offsets in a histogram; the song with the tallest spike wins

Here's the complete pipeline:

```
Audio Signal
    │
    ▼
┌─────────────────────────┐
│  Spectrogram (STFT)     │  Time × Frequency energy map
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Peak Extraction        │  Find the loudest points ("constellation")
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Combinatorial Pairing  │  Pair nearby peaks into fingerprints
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Hash Table             │  Store/lookup fingerprint → (song, position)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Offset Histogram       │  Find time-coherent matches → identify the song
└─────────────────────────┘
```

### Why hash tables?

A song library might contain millions of fingerprints. When you record a 5-second clip, it produces hundreds of fingerprints that all need to be looked up. Without a hash table, you'd need to scan every fingerprint in the database for each lookup — O(n) per query. With a hash table, each lookup is O(1) on average. That's the difference between "takes minutes" and "takes milliseconds."

---

## 2. Setup

### Prerequisites

- Python 3.9+
- A terminal / command line

### Virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate        # Windows
```

### Install dependencies

```bash
pip install -r requirements.txt
```

This installs: `numpy`, `scipy`, `matplotlib`, `sounddevice`, `pytest`, `loguru`

### Generate test songs

```bash
python scripts/generate_test_songs.py
```

This creates 5 synthetic WAV files in `songs/` that you can use for testing while developing.

### Run the tests

Your tests live in `tests/`. Initially, every test will fail with `NotImplementedError`. As you implement each function, more tests will pass:

```bash
# Run all tests
python -m pytest tests/ -v

# Run just the hash table tests
python -m pytest tests/test_hash_table.py -v

# Run just the fingerprint tests
python -m pytest tests/test_fingerprint.py -v

# Run just the matching tests
python -m pytest tests/test_matching.py -v
```

### Project structure

All the files you need to edit are in `src/`:

```
src/
├── hash_table.py          ← Milestone 1: implement the hash table
├── fingerprint.py         ← Milestone 2: implement peak finding & fingerprint generation
├── database.py            ← Milestone 3: implement song indexing & serialization
├── recognize.py           ← Milestone 3: implement the matching algorithm
└── utils.py               ← PROVIDED (audio I/O, plotting — no changes needed)
```

---

## 3. Milestone 1: The Hash Table

**Goal:** Build a hash table with separate chaining from scratch.

**File:** `src/hash_table.py`

**Tests:** `python -m pytest tests/test_hash_table.py -v`

### 3.1 Theory: What is a hash table?

A hash table is an array-based data structure that maps **keys** to **values** with O(1) average lookup time. The magic is in the **hash function** — a function that converts any key into an array index.

```
key ──► hash function ──► index ──► bucket (stores the value)
```

For example, if our array has 10 slots:
```
hash("apple") = 7   →  array[7] = "apple's data"
hash("banana") = 3  →  array[3] = "banana's data"
```

But what happens when two keys hash to the same index? That's a **collision**.

### 3.2 Theory: Collision handling with separate chaining

In **separate chaining**, each slot (bucket) in the array holds a *list* of all entries that hashed to that index:

```
Bucket 0: []
Bucket 1: [(key_x, val_x)]
Bucket 2: [(key_a, val_a), (key_b, val_b)]  ← collision! two entries share bucket 2
Bucket 3: [(key_y, val_y)]
Bucket 4: []
...
```

To **insert**: hash the key, append `(key, value)` to that bucket's list.

To **lookup**: hash the key, scan the bucket's list for entries with a matching key.

The average chain length is the **load factor** = `entries / capacity`. If the load factor stays low (we use a threshold of 0.75), most buckets have 0 or 1 entries, and lookup is O(1) on average.

### 3.3 Theory: Hash function design

A good hash function should:
1. Be **deterministic** — same key always produces the same index
2. Be **uniform** — distribute keys evenly across all buckets
3. Be **fast** — computed in O(1)

We'll use the **Knuth multiplicative hash**:

```
index = (key × 2654435761) mod capacity
```

The constant `2654435761` is a prime close to `2³² × φ` (where φ is the golden ratio). Knuth showed in *The Art of Computer Programming* that multiplying by this constant and taking the modulo distributes keys very evenly.

### 3.4 Theory: Why prime capacity?

Using a prime number for the array capacity reduces clustering. If the capacity is a power of 2, the modulo operation only looks at the lowest bits of the hash, so keys that differ only in their high bits will collide. A prime capacity uses information from all bits.

### 3.5 Theory: Resizing

When the load factor exceeds 0.75, chains get long and lookups slow down. The solution: **double the capacity** (to the next prime) and **rehash** every entry.

This is expensive — O(n) — but it happens rarely. Since we double each time, the total cost of all resizes over n insertions is O(n), giving an **amortized O(1)** cost per insertion.

### 3.6 Implementation steps

Open `src/hash_table.py`. Implement the methods in this order:

#### Step 1: `_hash(key)`

```python
def _hash(self, key):
    return (int(key) * 2654435761) % self._capacity
```

**Important:** Use `int(key)` to convert to a Python integer first. Later in the project, keys will come from numpy and can be `numpy.int64`, which overflows when multiplied by a large constant. Python's native `int` type has arbitrary precision, so no overflow.

#### Step 2: `insert(key, value)`

1. Compute the bucket index
2. Append `(key, value)` to that bucket
3. Increment `self._size`
4. If `load_factor() > 0.75`, call `self._resize()`

#### Step 3: `lookup(key)`

1. Compute the bucket index
2. Return a list of all values where the stored key matches

#### Step 4: `size()`, `capacity()`, `load_factor()`

These are one-liners — return `self._size`, `self._capacity`, and `self._size / self._capacity`.

#### Step 5: `_next_prime(n)`

Find the smallest prime ≥ n. This is a `@staticmethod` — no `self`.

Algorithm:
1. If n ≤ 2, return 2
2. Start at n (or n+1 if even)
3. Check if the candidate is prime: try dividing by all odd numbers from 3 to √candidate
4. If not prime, add 2 and try again

#### Step 6: `_resize()`

1. Compute new capacity: `_next_prime(self._capacity * 2)`
2. Save `old_buckets = self._buckets`
3. Reset: new buckets, `self._size = 0`, update `self._capacity`
4. Re-insert every `(key, value)` from old buckets using `self.insert()`

#### Step 7: `stats()`

Return a dict with these keys:
- `"capacity"`, `"size"`, `"load_factor"` (rounded to 4 decimals)
- `"empty_buckets"`: count of buckets with length 0
- `"max_chain_length"`: longest chain
- `"avg_chain_length"`: average of non-empty chains (rounded to 4 decimals)

### 3.7 Checkpoint

Run the tests:
```bash
python -m pytest tests/test_hash_table.py -v
```

All 11 tests should pass. If they do, your hash table is ready for Shazam!

---

## 4. Milestone 2: Audio Fingerprinting

**Goal:** Extract fingerprints from audio — the "constellation map" that makes each song recognizable.

**File:** `src/fingerprint.py`

**Tests:** `python -m pytest tests/test_fingerprint.py -v`

### 4.1 Theory: The spectrogram

Raw audio is a 1D signal — a sequence of amplitude values over time. To identify a song, we need to know *which frequencies are present at each moment*. The **Short-Time Fourier Transform (STFT)** converts the 1D signal into a 2D **spectrogram**:

```
         Frequency
            ▲
            │  ░░░░      ░░░░
            │  ████      ████
            │  ████░░░░░░████
            │  ░░████████░░░░
            │  ░░░░░░░░░░░░░░
            └──────────────────► Time
```

Each cell represents the energy at a specific frequency and time. Bright spots are loud frequencies; dark areas are quiet.

**DS&A connection:** The FFT at the heart of the STFT is a classic divide-and-conquer algorithm: O(n log n) instead of the naive O(n²).

The `compute_spectrogram()` function is **provided for you** — it calls scipy's STFT and converts the result to dB scale. You don't need to implement it, but you should understand what it returns:
- `freqs`: array of frequency values (Hz) for each row
- `times`: array of time values (seconds) for each column
- `spec`: 2D matrix of shape `(freq_bins, time_bins)` in dB

#### Visualize it

Try this in a Python shell to see what a spectrogram looks like:

```python
from src.utils import load_audio, plot_spectrogram

audio, sr = load_audio("songs/rock_power.wav")
plot_spectrogram(audio, sr, title="Rock Power")
```

### 4.2 Theory: Peak extraction — the constellation map

The spectrogram has thousands of cells, but only the **peaks** (local maxima) matter. These peaks are the "constellation points" — the distinctive landmarks that identify a song.

```
         Frequency
            ▲
            │        ★            ★ = peak (landmark)
            │  ★           ★
            │        ★
            │  ★                 ★
            │              ★
            └──────────────────► Time
```

#### Why band-based extraction?

When audio plays through speakers and gets recorded by a microphone, the acoustic path can shift which exact frequency bin has the most energy. A peak might move from bin 42 to bin 44. If we required peaks to be exact local maxima, this shift would break recognition.

The solution: divide the frequency axis into **logarithmic bands** and pick the loudest bin **within each band** for every time frame. A peak only needs to remain the loudest in its band — not at the exact same bin. This is much more robust.

The bands are logarithmically spaced to match human hearing:
```
Band 1:  bins   1 -  10  (low bass)
Band 2:  bins  10 -  20
Band 3:  bins  20 -  40
Band 4:  bins  40 -  80
Band 5:  bins  80 - 160
Band 6:  bins 160 - 256
Band 7:  bins 256 - 384
Band 8:  bins 384 - 512  (high treble)
```

Low frequencies get narrow bands (more precision where music has its fundamentals), high frequencies get wide bands.

#### Percentile thresholding

We only keep peaks above the 60th percentile of the entire spectrogram. This filters out quiet background noise while keeping the strong, distinctive peaks. Using a percentile (instead of a fixed amplitude) makes the system volume-independent.

#### Local maximum filter

After band-based selection, we apply a **local maximum filter** to remove temporally redundant peaks. A sustained note would otherwise create a peak at every single time frame — we only want to keep the strongest instance.

### 4.3 Implementation: `find_peaks()`

Open `src/fingerprint.py`. The `find_peaks()` function has two steps:

#### Step 1: Band-based candidate selection

```python
band_peaks = set()
for t in range(n_time):
    col = spec[:, t]                  # the entire frequency column at time t
    for lo, hi in freq_bands:
        hi = min(hi, n_freq)          # clamp to spectrogram size
        if lo >= n_freq:
            break
        band_slice = col[lo:hi]       # just this band
        f_local = np.argmax(band_slice)  # loudest bin within the band
        f_global = lo + f_local       # convert to global index
        if col[f_global] > threshold: # above percentile threshold?
            band_peaks.add((t, f_global))
```

#### Step 2: Local maximum filter

```python
local_max = maximum_filter(spec, size=(neighborhood_freq, neighborhood_time))
peaks = []
for t, f in band_peaks:
    if spec[f, t] == local_max[f, t]:      # is it a true local max?
        peaks.append((int(t), int(f)))
```

Note the index order: `spec` is indexed as `[freq, time]`, but peaks are stored as `(time, freq)`.

#### Visualize it

After implementing, try:
```python
from src.utils import load_audio, plot_constellation
audio, sr = load_audio("songs/rock_power.wav")
plot_constellation(audio, sr, title="Rock Power — Constellation")
```

You should see red dots (peaks) overlaid on the spectrogram.

### 4.4 Theory: Why pair peaks?

A single peak is not very distinctive — many songs have energy at 440 Hz. But a *pair* of peaks is much more specific:

> "440 Hz followed by 880 Hz, 5 time bins later"

This is unlikely to happen at the exact same position in two different songs. By pairing peaks, we create **fingerprints** that are highly discriminative.

Each pair produces a fingerprint:
```
hash_value = hash_peak_pair(anchor_freq, paired_freq, time_delta)
offset     = anchor_time
```

The hash value becomes the **key** in our hash table. The offset tells us *where in the song* this fingerprint occurs.

### 4.5 Theory: Bit packing — `hash_peak_pair()`

The `hash_peak_pair(f1, f2, dt)` function encodes two peaks into a single integer using **bit packing**. This integer becomes the key in our hash table.

We pack three values using bit shifts:

```
h = (f1 << (FREQ_BITS + DELTA_BITS)) | (f2 << DELTA_BITS) | dt
```

With `FREQ_BITS = 12` and `DELTA_BITS = 12`:

```
Bit layout (36 bits total):
┌──────────────┬──────────────┬──────────────┐
│  f1 (12 bits) │  f2 (12 bits) │  dt (12 bits) │
└──────────────┴──────────────┴──────────────┘

Example: f1=100, f2=200, dt=5
  100 << 24 = 1677721600
  200 << 12 = 819200
  5          = 5
  h = 1677721600 | 819200 | 5 = 1678540805
```

**Why bit packing?** It produces a single integer key from three values while keeping them all recoverable. The choice of *what goes into the hash* directly affects collision rate and matching accuracy.

**DS&A connection:** This is the core lesson — you're designing a hash function that encodes domain-specific information. If you dropped f2, you'd get more collisions (less specific). If you used too many bits for dt, you'd waste space. The triplet (f1, f2, dt) is the sweet spot.

### 4.6 Implementation: `hash_peak_pair()`

This is a one-liner — just the bit-packing formula:

```python
def hash_peak_pair(f1, f2, dt):
    return (f1 << (FREQ_BITS + DELTA_BITS)) | (f2 << DELTA_BITS) | dt
```

### 4.7 Implementation: `generate_fingerprints()`

For each "anchor" peak, pair it with up to `FAN_OUT` (15) future peaks within a "target zone":

```
         Frequency
            ▲
            │     ┌─────────────────┐
            │     │  Target Zone     │
            │  ★──│───────────★     │   ★ anchor, ★ paired peak
            │     │        ★        │
            │     │  ★              │
            │     └─────────────────┘
            └──────────────────────────► Time
                  ↑                 ↑
              zone_start        zone_end
              (1 bin)           (50 bins)
```

```python
peaks = sorted(peaks, key=lambda p: (p[0], p[1]))
fingerprints = []

for i, (t1, f1) in enumerate(peaks):
    paired = 0
    for j in range(i + 1, len(peaks)):
        t2, f2 = peaks[j]
        dt = t2 - t1
        if dt < zone_start:
            continue                  # too close, skip
        if dt > zone_end:
            break                     # too far, stop
        h = hash_peak_pair(f1, f2, dt)
        fingerprints.append((h, t1))
        paired += 1
        if paired >= fan_out:
            break                     # enough pairs for this anchor

return fingerprints
```

### 4.8 Checkpoint

```bash
python -m pytest tests/test_fingerprint.py -v
```

All 8 tests should pass.

---

## 5. Milestone 3: Indexing and Matching

**Goal:** Build a song database and implement the matching algorithm.

**Files:** `src/database.py` and `src/recognize.py`

**Tests:** `python -m pytest tests/test_matching.py -v`

### 5.1 The database

The `SongDatabase` class wraps your hash table:

```
Hash Table contents after indexing 3 songs:

  hash_key → [(song_0, time_42), (song_2, time_108)]
  hash_key → [(song_1, time_7)]
  hash_key → [(song_0, time_99), (song_1, time_55), (song_2, time_3)]
  ...
```

Multiple songs (and multiple positions within the same song) can share the same fingerprint hash. This is exactly the separate-chaining scenario — and it's why your hash table stores *lists* of values, not single values.

### 5.2 Implementation: `index_song()` and `index_directory()`

These are in `src/database.py`. Follow the detailed docstrings in the file.

`index_song()`:
1. Load audio → fingerprint it → assign a song ID → store name → insert all fingerprints into the hash table

`index_directory()`:
1. List `.wav` files → sort → call `index_song()` for each

### 5.3 Theory: The matching algorithm

This is the most elegant part of the system. When you record a 5-second clip:

1. Fingerprint the clip → get a list of `(hash, t_clip)` pairs
2. Look up each hash in the database → for each hit `(song_id, t_song)`, compute the **offset delta**: `t_song - t_clip`
3. Group deltas by song. For the *correct* song, these deltas will cluster around the same value (because the clip's fingerprints align with the song at a consistent time offset)
4. Build a **histogram** of deltas for each song → the song with the tallest spike wins

#### Why time coherence matters

Imagine your clip starts at second 30 of "Billie Jean." Every matching fingerprint will have:
```
delta = t_song - t_clip ≈ constant (≈ 30 seconds worth of time bins)
```

Random false matches from other songs will have scattered, random deltas. So:

```
Billie Jean histogram:        Other Song histogram:
  count                         count
    │                             │
  20│     █                     2 │ █  █  █  █  █  █
    │     █                       │ █  █  █  █  █  █
    │  █  █  █                    └──────────────────► delta
    └──────────► delta
    (clear spike = match!)        (flat noise = no match)
```

**DS&A connection:** Building the histogram is itself a hash table operation! You're mapping `delta → count`. The pseudocode uses a Python dict for this inner histogram, but conceptually it's the same structure you just built.

### 5.4 Implementation: `recognize()`

Open `src/recognize.py`. The algorithm:

```python
def recognize(audio, sample_rate, database):
    fingerprints = fingerprint_audio(audio, sample_rate)
    if not fingerprints:
        return None, 0, {}

    # Collect offset deltas grouped by song
    matches = {}  # song_id → list of deltas
    for hash_val, t_clip in fingerprints:
        hits = database.table.lookup(hash_val)
        for song_id, t_song in hits:
            delta = t_song - t_clip
            matches.setdefault(song_id, []).append(delta)

    if not matches:
        return None, 0, {}

    # For each song, build offset histogram and find peak count
    best_song_id = None
    best_count = 0
    all_scores = {}

    for song_id, deltas in matches.items():
        histogram = {}
        for d in deltas:
            histogram[d] = histogram.get(d, 0) + 1
        peak_count = max(histogram.values())
        song_name = database.get_song_name(song_id)
        all_scores[song_name] = peak_count
        if peak_count > best_count:
            best_count = peak_count
            best_song_id = song_id

    best_name = database.get_song_name(best_song_id) if best_song_id is not None else None
    return best_name, best_count, all_scores
```

### 5.5 Implementation: `save()` and `load()`

These let you serialize the database to JSON so you don't have to re-index every time. Follow the detailed docstrings in `database.py`.

Key gotcha: numpy integers are not JSON-serializable. Always use `int()` to convert:
```python
entries.append([int(key), int(song_id), int(time_offset)])
```

### 5.6 Checkpoint

```bash
python -m pytest tests/test_matching.py -v
```

All 6 tests should pass. Try a quick end-to-end test:

```python
from src.database import SongDatabase
from src.recognize import recognize
from src.utils import load_audio

# Index songs
db = SongDatabase()
db.index_directory("songs/")

# Recognize a clip
audio, sr = load_audio("songs/rock_power.wav")
clip = audio[int(3 * sr):int(8 * sr)]  # 5-second clip
name, score, scores = recognize(clip, sr, db)
print(f"Match: {name} (score: {score})")
print(f"Hash table stats: {db.table.stats()}")
```

---

## 6. Milestone 4: Live Recognition

**Goal:** Record from the microphone and identify a song playing nearby.

No new code to implement — `record_and_recognize()` in `recognize.py` is provided. But this is where everything comes together.

### 6.1 Adding real songs

Synthetic test songs are fine for unit tests, but the real test is recognizing real music. To add songs:

1. Place MP3 files in `songs/source/`
2. Convert to mono 22050 Hz WAV:
   ```bash
   bash scripts/convert_songs.sh
   ```
3. Rebuild the database:
   ```bash
   python scripts/build_database.py
   ```

### 6.2 Test your microphone

```bash
python scripts/test_audio.py
```

This records 5 seconds and plays it back. Make sure you can hear yourself.

### 6.3 Live recognition

```python
from src.database import SongDatabase
from src.recognize import record_and_recognize

db = SongDatabase.load("data/database.json")
record_and_recognize(db, duration=5)
```

Play a song on your phone near the microphone, run the code, and see if it identifies the song!

### 6.4 Experiments to try

- **Distance:** How far can the phone be from the mic?
- **Volume:** How quiet can the song be?
- **Noise:** Does it still work in a noisy room?
- **Duration:** Try 3 seconds vs. 10 seconds — how does the score change?
- **Clip position:** Does it matter what part of the song is playing?

---

## 7. Discussion Questions

Answer these based on your implementation. Use data from your hash table statistics to support your answers.

1. **Hash function design:** Why do we hash the triplet (f1, f2, Δt) rather than just a single frequency? What happens to collision rate and matching accuracy if you drop one component? Try it and measure.

2. **Collision analysis:** After indexing all songs, what is the load factor? What is the longest chain? How does this compare to the expected O(1) average lookup?

3. **Capacity & primes:** Why is the initial capacity a prime number? What happens to collision distribution if you use a power of 2 instead? Modify `DEFAULT_CAPACITY` to 10000 (not prime), re-index, and compare `stats()`.

4. **Resizing cost:** When the table resizes, what is the time complexity? How often does it happen, and what is the amortized cost per insertion?

5. **Fan-out trade-off:** Increasing `FAN_OUT` creates more fingerprints per anchor. How does this affect:
   - Storage (hash table size)?
   - Indexing time?
   - Recognition accuracy?
   Try `FAN_OUT = 5` vs. `FAN_OUT = 30` and compare.

6. **Robustness:** Why does the system still work when the recording has background noise, different volume, or starts at an arbitrary point in the song? Which specific design choices enable this?

7. **Time coherence:** Why is the offset histogram step necessary? Why can't we just count raw hash matches per song? Construct a scenario where raw counting would give the wrong answer but the histogram gives the right one.

---

## 8. Reference

### Key parameters (in `fingerprint.py`)

| Parameter | Value | Purpose |
|---|---|---|
| `SAMPLE_RATE` | 22050 Hz | Audio sample rate |
| `FFT_WINDOW_SIZE` | 2048 | Samples per FFT window |
| `HOP_SIZE` | 1024 | Window step size (50% overlap) |
| `PEAK_NEIGHBORHOOD_TIME` | 7 | Local-max filter width (time) |
| `PEAK_NEIGHBORHOOD_FREQ` | 7 | Local-max filter width (frequency) |
| `MIN_PERCENTILE` | 60 | Peak threshold (percentile of spectrogram) |
| `FREQ_BANDS` | 8 log bands | Band-based peak extraction ranges |
| `FAN_OUT` | 15 | Max pairs per anchor peak |
| `TARGET_ZONE_START` | 1 | Min time-bin gap for pairing |
| `TARGET_ZONE_END` | 50 | Max time-bin gap for pairing |
| `FREQ_BITS` | 12 | Bits for frequency in hash |
| `DELTA_BITS` | 12 | Bits for time delta in hash |

### Files you implement

| File | What you implement |
|---|---|
| `hash_table.py` | `_hash`, `insert`, `lookup`, `size`, `capacity`, `load_factor`, `stats`, `_next_prime`, `_resize` |
| `fingerprint.py` | `find_peaks`, `hash_peak_pair`, `generate_fingerprints` |
| `database.py` | `index_song`, `index_directory`, `save`, `load` |
| `recognize.py` | `recognize` |

### Files provided for you

| File | What it does |
|---|---|
| `utils.py` | Audio loading, resampling, filtering, plotting |
| `fingerprint.py` | `compute_spectrogram` (the STFT call), `fingerprint_audio` (chains the pipeline) |
| `recognize.py` | `record_and_recognize` (mic recording wrapper) |

### Running tests

```bash
# All student tests
python -m pytest tests/ -v

# By milestone
python -m pytest tests/test_hash_table.py -v      # Milestone 1
python -m pytest tests/test_fingerprint.py -v      # Milestone 2
python -m pytest tests/test_matching.py -v          # Milestone 3
```

### Academic references

- Wang, A. (2003). *"An Industrial-Strength Audio Search Algorithm."* Proc. ISMIR.
- Knuth, D. (1997). *The Art of Computer Programming, Vol. 3: Sorting and Searching.* — Multiplicative hashing.

## External Tools

- [Spectrogram Visualizer](https://spectrogram.sciencemusic.org/)
