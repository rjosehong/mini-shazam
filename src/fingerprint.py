"""
Audio fingerprinting module.

Handles: spectrogram computation, peak extraction, and combinatorial
fingerprint generation.

Refer to GUIDE.md, Milestone 2 for detailed instructions.
"""

import numpy as np
from scipy.ndimage import maximum_filter
from scipy.signal import stft

# ------------------------------------------------------------------ #
# Parameters (you can tune these — see GUIDE.md for explanations)
# ------------------------------------------------------------------ #
SAMPLE_RATE = 22050          # samples per second
FFT_WINDOW_SIZE = 2048       # samples per FFT window
HOP_SIZE = 1024              # samples between consecutive windows
PEAK_NEIGHBORHOOD_TIME = 7   # time bins for local max filter
PEAK_NEIGHBORHOOD_FREQ = 7   # freq bins for local max filter
MIN_PERCENTILE = 60          # only keep peaks above this percentile

# Frequency bands for band-based peak extraction (bin indices).
# These are logarithmically spaced to match human hearing:
# low frequencies get narrow bands (more precision where music
# has its fundamentals), high frequencies get wide bands.
FREQ_BANDS = [
    (1, 10), (10, 20), (20, 40), (40, 80), (80, 160),
    (160, 256), (256, 384), (384, 512),
]

FAN_OUT = 15                 # max number of pairs per anchor peak
TARGET_ZONE_START = 1        # earliest time-bin offset for pairing
TARGET_ZONE_END = 50         # latest time-bin offset for pairing
FREQ_BITS = 12               # bits allocated to each frequency in the hash
DELTA_BITS = 12              # bits allocated to the time delta in the hash


# ------------------------------------------------------------------ #
# Step 1: Spectrogram — PROVIDED FOR YOU
# ------------------------------------------------------------------ #

def compute_spectrogram(audio, sample_rate=SAMPLE_RATE):
    """
    Compute the magnitude spectrogram using the Short-Time Fourier Transform.

    This function is provided for you. It:
      1. Applies the STFT to break audio into overlapping time windows
      2. Computes the magnitude (energy) at each time-frequency bin
      3. Converts to dB scale for proper dynamic range compression
      4. Normalizes so the maximum is 0 dB

    The dB conversion is critical: it makes peak detection work regardless
    of recording volume. A peak 20dB above its neighbors looks the same
    whether the overall signal is loud or quiet.

    Returns:
        freqs: 1-D array of frequency bin centres (Hz)
        times: 1-D array of time bin centres (seconds)
        spec:  2-D magnitude matrix (freq_bins x time_bins), in dB
    """
    freqs, times, Zxx = stft(
        audio,
        fs=sample_rate,
        nperseg=FFT_WINDOW_SIZE,
        noverlap=FFT_WINDOW_SIZE - HOP_SIZE,
    )
    magnitude = np.abs(Zxx)
    # Convert to dB scale
    magnitude = 10 * np.log10(magnitude + 1e-10)
    # Normalize so max is 0 dB
    magnitude -= magnitude.max()
    return freqs, times, magnitude


# ------------------------------------------------------------------ #
# Step 2: Peak extraction — YOU IMPLEMENT THIS
# ------------------------------------------------------------------ #

def find_peaks(spec, neighborhood_freq=PEAK_NEIGHBORHOOD_FREQ,
               neighborhood_time=PEAK_NEIGHBORHOOD_TIME,
               min_percentile=MIN_PERCENTILE,
               freq_bands=FREQ_BANDS):
    """
    Find peaks in the spectrogram using a band-based approach.

    This is the most important function for recognition quality.
    The algorithm has two steps:

    STEP 1 — Band-based candidate selection:
      For each time frame (column of the spectrogram), look at each
      frequency band separately. Within each band, find the loudest
      frequency bin. If that bin's value is above the percentile
      threshold, add it as a candidate peak.

      Why bands? When audio travels through speakers and a microphone,
      the exact frequency bin of a peak may shift slightly. But it will
      almost always remain the loudest bin *within its frequency band*.
      This makes the system robust to acoustic distortion.

    STEP 2 — Local maximum filter:
      Apply scipy's maximum_filter to the spectrogram with the given
      neighborhood size. A point is a local maximum if its value equals
      the maximum_filter output at that position. Only keep candidate
      peaks from Step 1 that pass this local-max test.

      This removes temporally redundant peaks (e.g., a sustained note
      that would otherwise create a peak at every single time frame).

    Args:
        spec: 2D numpy array (freq_bins x time_bins) — the spectrogram
        neighborhood_freq: size of the local-max filter in frequency axis
        neighborhood_time: size of the local-max filter in time axis
        min_percentile: only keep peaks above this percentile of spec values
        freq_bands: list of (low_bin, high_bin) tuples defining frequency bands

    Returns:
        List of (time_bin, freq_bin) tuples — the constellation points.
    """
    n_freq, n_time = spec.shape

    # Compute the threshold: the value at the given percentile
    threshold = np.percentile(spec, min_percentile)

    # -------------------------------------------------------------- #
    # STEP 1: For each time frame, pick the loudest bin per band
    # -------------------------------------------------------------- #
    band_peaks = set()

    # TODO: Implement band-based peak selection
    #
    # For each time frame t in range(n_time):
    #   For each (lo, hi) in freq_bands:
    #     - Clamp hi to n_freq (in case the spectrogram is smaller than the band)
    #     - Skip if lo >= n_freq
    #     - Extract the slice of the column: spec[lo:hi, t]
    #     - Find the index of the maximum value within that slice (np.argmax)
    #     - Convert back to a global frequency index: f_global = lo + f_local
    #     - If spec[f_global, t] > threshold, add (t, f_global) to band_peaks
    
    for t in range(n_time):
        for lo, hi in freq_bands:
            hi = min(hi, n_freq)  # Clamp hi to n_freq
            if lo >= n_freq:       # Skip if band starts beyond spectrogram
                continue
            band_slice = spec[lo:hi, t]
            f_local = np.argmax(band_slice)
            f_global = lo + f_local
            if spec[f_global, t] > threshold:
                band_peaks.add((t, f_global))

    find_peaks_stats = {
        "threshold": threshold,
        "band_peaks": len(band_peaks)
    }

    # -------------------------------------------------------------- #
    # STEP 2: Apply local-max filter to remove redundant peaks
    # -------------------------------------------------------------- #

    # TODO: Implement local-max filtering
    #
    # 1. Compute the local maximum filter over the entire spectrogram:
    #    local_max = maximum_filter(spec, size=(neighborhood_freq, neighborhood_time))
    #
    # 2. Filter band_peaks: keep only (t, f) where spec[f, t] == local_max[f, t]
    #    (Note: spec is indexed as [freq, time] but peaks are stored as (time, freq))
    #
    # 3. Return the filtered peaks as a list of (int(t), int(f)) tuples
    
    local_max = maximum_filter(spec, size=(neighborhood_freq, neighborhood_time))
    filtered_peaks = []
    for t, f in band_peaks:
        if spec[f, t] == local_max[f, t]:
            filtered_peaks.append((int(t), int(f)))
    
    find_peaks_stats["final_peaks"] = len(filtered_peaks)
    print("find_peaks stats:", find_peaks_stats)
    return filtered_peaks


# ------------------------------------------------------------------ #
# Step 3: Hash two peaks into a fingerprint — YOU IMPLEMENT THIS
# ------------------------------------------------------------------ #

def hash_peak_pair(f1, f2, dt):
    """
    Encode two peaks into a single integer fingerprint hash.

    A single peak (one frequency at one time) is not very distinctive —
    many songs have energy at 440 Hz. But a PAIR of peaks is much more
    specific: "440 Hz followed by 880 Hz, 5 time bins later" is unlikely
    to occur at the same position in two different songs.

    We encode the pair as a single integer using bit packing:

        hash = (f1 << (FREQ_BITS + DELTA_BITS)) | (f2 << DELTA_BITS) | dt

    This lays out three values in the bits of one integer:

        ┌──────────────┬──────────────┬──────────────┐
        │  f1 (12 bits) │  f2 (12 bits) │  dt (12 bits) │
        └──────────────┴──────────────┴──────────────┘
        ← high bits                        low bits →

    Example: f1=100, f2=200, dt=5
        100 << 24 = 1677721600
        200 << 12 = 819200
        5          = 5
        hash = 1677721600 | 819200 | 5 = 1678540805

    Why bit packing? It produces a single integer key for our hash table
    while preserving all three components. The choice of WHAT goes into
    the hash (f1, f2, dt) directly affects collision rate and matching
    accuracy — this is the core hash function design decision.

    Args:
        f1: Frequency bin of the anchor peak
        f2: Frequency bin of the paired peak
        dt: Time difference (in bins) between the two peaks

    Returns:
        A single integer encoding the peak pair.
    """
    # TODO: Implement the bit-packing formula
    #
    h = (f1 << (FREQ_BITS + DELTA_BITS)) | (f2 << DELTA_BITS) | dt
    return h


# ------------------------------------------------------------------ #
# Step 4: Fingerprint generation — YOU IMPLEMENT THIS
# ------------------------------------------------------------------ #

def generate_fingerprints(peaks, fan_out=FAN_OUT,
                          zone_start=TARGET_ZONE_START,
                          zone_end=TARGET_ZONE_END):
    """
    Pair each anchor peak with nearby future peaks to create fingerprints.

    For each "anchor" peak, we pair it with up to `fan_out` future peaks
    within a "target zone" (between zone_start and zone_end time bins away).

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

    For each valid pair, we call hash_peak_pair(f1, f2, dt) to produce the
    hash key, and store (hash_key, anchor_time) as the fingerprint.

    Args:
        peaks: List of (time_bin, freq_bin) tuples from find_peaks()
        fan_out: Maximum number of pairs per anchor peak
        zone_start: Minimum time-bin gap between anchor and paired peak
        zone_end: Maximum time-bin gap between anchor and paired peak

    Returns:
        List of (hash_value, anchor_time) tuples.
        - hash_value: the integer from hash_peak_pair()
        - anchor_time: the time bin of the anchor peak (used as the "offset")
    """
    # Sort peaks by time, then frequency
    peaks = sorted(peaks, key=lambda p: (p[0], p[1]))
    fingerprints = []

    # TODO: Implement combinatorial fingerprint generation
    #
    # For each peak i (the anchor) at (t1, f1):
    #   paired = 0
    #   For each subsequent peak j at (t2, f2):
    #     dt = t2 - t1
    #     if dt < zone_start: continue (too close, skip)
    #     if dt > zone_end: break (too far, stop looking)
    #     h = hash_peak_pair(f1, f2, dt)
    #     Append (h, t1) to fingerprints
    #     paired += 1
    #     if paired >= fan_out: break
    
    for i in range(len(peaks)):
        t1, f1 = peaks[i]
        paired = 0
        for j in range(i + 1, len(peaks)):
            t2, f2 = peaks[j]
            dt = t2 - t1
            if dt < zone_start:
                continue
            if dt > zone_end:
                break
            h = hash_peak_pair(f1, f2, dt)
            fingerprints.append((h, t1))
            paired += 1
            if paired >= fan_out:
                break

    generate_fingerprints_stats = {
        "total_peaks": len(peaks),
        "total_fingerprints": len(fingerprints)
    }
    print("generate_fingerprints stats:", generate_fingerprints_stats)


    return fingerprints


# ------------------------------------------------------------------ #
# Full pipeline — PROVIDED FOR YOU
# ------------------------------------------------------------------ #

def fingerprint_audio(audio, sample_rate=SAMPLE_RATE):
    """
    Full pipeline: audio signal -> list of (hash_value, time_offset).

    This just chains the three steps together:
      1. compute_spectrogram
      2. find_peaks
      3. generate_fingerprints
    """
    _, _, spec = compute_spectrogram(audio, sample_rate)
    peaks = find_peaks(spec)
    return generate_fingerprints(peaks)