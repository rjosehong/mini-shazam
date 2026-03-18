"""
Utility functions: audio loading, resampling, filtering, and plotting.

This module is provided for you — no implementation needed here.
It handles audio I/O and visualization so you can focus on the
core data structures and algorithms.
"""

import wave

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.signal import resample as scipy_resample

from src.fingerprint import SAMPLE_RATE, compute_spectrogram, find_peaks


def load_audio(filepath, target_sr=SAMPLE_RATE):
    """
    Load a WAV file and return (samples, sample_rate).

    - Reads raw bytes and converts to a numpy float64 array
    - Mixes multi-channel audio down to mono
    - Normalizes amplitude to [-1, 1]
    - Resamples to target_sr if the file's sample rate differs

    Args:
        filepath: Path to a .wav file
        target_sr: Desired sample rate (default: SAMPLE_RATE from fingerprint.py)

    Returns:
        (audio, sample_rate) — 1D numpy array and integer sample rate
    """
    with wave.open(filepath, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    # Convert raw bytes to numpy array
    if sampwidth == 1:
        dtype = np.uint8
    elif sampwidth == 2:
        dtype = np.int16
    elif sampwidth == 4:
        dtype = np.int32
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")

    audio = np.frombuffer(raw, dtype=dtype).astype(np.float64)

    # Mix to mono
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    # Normalize to [-1, 1]
    max_val = np.iinfo(dtype).max if dtype != np.float64 else 1.0
    audio = audio / max_val

    # Resample with proper anti-aliasing
    if framerate != target_sr:
        n_target = int(len(audio) * target_sr / framerate)
        audio = scipy_resample(audio, n_target)

    return audio, target_sr


def highpass_filter(audio, cutoff=200, sample_rate=SAMPLE_RATE, order=4):
    """
    Apply a high-pass Butterworth filter to remove low-frequency rumble.

    This removes frequencies below `cutoff` Hz — things like HVAC hum,
    handling noise, and other low-frequency interference that doesn't
    help with song recognition.
    """
    sos = butter(order, cutoff, btype="high", fs=sample_rate, output="sos")
    return sosfilt(sos, audio)


def plot_spectrogram(
    audio, sample_rate=SAMPLE_RATE, title="Spectrogram", start=0.0, duration=1.0
):
    """
    Plot the magnitude spectrogram as a heatmap.

    Args:
        audio: 1D numpy array of audio samples
        sample_rate: sample rate in Hz
        title: plot title
        start: start time in seconds (default: 0.0)
        duration: how many seconds to display (default: 1.0)
    """
    freqs, times, spec = compute_spectrogram(audio, sample_rate)
    # Select the time window
    t_mask = (times >= start) & (times < start + duration)
    times = times[t_mask]
    spec = spec[:, t_mask]

    plt.figure(figsize=(12, 5))
    plt.pcolormesh(times, freqs, spec, shading="auto")
    plt.colorbar(label="dB")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title(title)
    plt.tight_layout()
    plt.show()


def plot_constellation(
    audio, sample_rate=SAMPLE_RATE, title="Constellation Map", start=0.0, duration=1.0
):
    """
    Plot the spectrogram with peak landmarks overlaid as red dots.

    Args:
        audio: 1D numpy array of audio samples
        sample_rate: sample rate in Hz
        title: plot title
        start: start time in seconds (default: 0.0)
        duration: how many seconds to display (default: 1.0)
    """
    freqs, times, spec = compute_spectrogram(audio, sample_rate)
    peaks = find_peaks(spec)

    t_mask = (times >= start) & (times < start + duration)
    times_w = times[t_mask]
    spec_w = spec[:, t_mask]

    plt.figure(figsize=(12, 5))
    plt.pcolormesh(times_w, freqs, spec_w, shading="auto", alpha=0.5)
    if peaks:
        t_vals = [times[t] for t, f in peaks if start <= times[t] < start + duration]
        f_vals = [freqs[f] for t, f in peaks if start <= times[t] < start + duration]
        plt.scatter(t_vals, f_vals, c="red", s=5, marker="x")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title(title)
    plt.tight_layout()
    plt.show()


def plot_match_histogram(deltas, title="Offset Histogram"):
    """
    Plot a histogram of time-offset deltas for a match candidate.

    A tall, narrow spike in this histogram means many fingerprints
    agree on the same time alignment — strong evidence of a match.
    """
    if not deltas:
        print("No deltas to plot.")
        return
    plt.figure(figsize=(10, 4))
    plt.hist(deltas, bins=max(len(set(deltas)), 1), edgecolor="black")
    plt.xlabel("Time offset delta")
    plt.ylabel("Count")
    plt.title(title)
    plt.tight_layout()
    plt.show()
