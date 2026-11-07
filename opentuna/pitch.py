"""FFT accelerated YIN pitch detection, derived from OpenTuna's audio engine."""
import numpy as np


def detect_pitch(data, sample_rate=44100, low=60, high=1200, noise_gate=.008):
    signal = np.asarray(data, dtype=np.float64).reshape(-1)
    if len(signal) < 64 or not np.all(np.isfinite(signal)):
        return 0.0
    signal = signal - signal.mean()
    if np.sqrt(np.mean(signal * signal)) < noise_gate:
        return 0.0
    max_lag = min(int(sample_rate / low), len(signal) // 2)
    min_lag = max(2, int(sample_rate / high))
    if max_lag <= min_lag + 2:
        return 0.0
    size = 1 << (2 * len(signal) - 1).bit_length()
    spectrum = np.fft.rfft(signal, n=size)
    corr = np.fft.irfft(spectrum * spectrum.conjugate(), n=size)[:max_lag + 1]
    energy = np.concatenate(([0.], np.cumsum(signal * signal)))
    lags = np.arange(max_lag + 1)
    difference = np.maximum(0, energy[len(signal) - lags] + energy[-1] - energy[lags] - 2 * corr)
    normalized = np.ones(max_lag + 1)
    normalized[1:] = difference[1:] * lags[1:] / np.maximum(np.cumsum(difference[1:]), 1e-15)
    candidates = np.flatnonzero(normalized[min_lag:max_lag] < .15)
    if not len(candidates):
        return 0.0
    peak = int(candidates[0] + min_lag)
    while peak + 1 < max_lag and normalized[peak + 1] < normalized[peak]:
        peak += 1
    left, middle, right = normalized[peak - 1:peak + 2]
    denominator = left - 2 * middle + right
    offset = .5 * (left - right) / denominator if abs(denominator) > 1e-12 else 0
    frequency = float(sample_rate / (peak + np.clip(offset, -.5, .5)))
    return frequency if low <= frequency <= high else 0.0
