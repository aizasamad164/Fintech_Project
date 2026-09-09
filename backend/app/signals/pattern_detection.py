"""
FR-3.1: Detect price support/resistance and breakout formations
using scipy.signal.find_peaks.
"""
import numpy as np
from scipy.signal import find_peaks


def detect_support_resistance(close_prices: np.ndarray) -> dict:
    """
    Returns detected peak (resistance) and trough (support) indices.
    """
    peaks, _ = find_peaks(close_prices)
    troughs, _ = find_peaks(-close_prices)
    return {"resistance_idx": peaks, "support_idx": troughs}
