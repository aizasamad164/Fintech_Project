import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from app.signals.pattern_detection import (
    analyze_patterns,
    detect_breakouts,
    detect_support_resistance,
    to_pattern_records,
)


def _oscillating_prices(n: int = 200) -> np.ndarray:
    """Clean sine wave: resistance at exactly 105, support at exactly 95."""
    return 100 + 5 * np.sin(2 * np.pi * np.arange(n) / 20)


def _as_frame(close: np.ndarray, volume: float = 1_000_000) -> pd.DataFrame:
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": volume},
        index=pd.bdate_range(end="2026-09-18", periods=len(close)),
    )


def test_levels_are_clustered_into_single_resistance_and_support():
    result = detect_support_resistance(_oscillating_prices())

    assert len(result["resistance_levels"]) == 1
    assert len(result["support_levels"]) == 1
    resistance = result["resistance_levels"][0]
    support = result["support_levels"][0]
    assert abs(resistance["price"] - 105) < 0.01
    assert abs(support["price"] - 95) < 0.01
    assert resistance["touches"] >= 5
    assert support["touches"] >= 5


def test_prominence_filter_ignores_noise():
    rng = np.random.default_rng(1)
    noisy = 100 + np.cumsum(rng.normal(0, 0.2, 300))

    raw_peaks, _ = find_peaks(noisy)
    filtered = detect_support_resistance(noisy)["resistance_idx"]

    assert len(filtered) < len(raw_peaks)


def test_too_short_series_returns_empty_result():
    result = detect_support_resistance(np.array([1.0, 2.0, 1.5]))
    assert result["resistance_levels"] == []
    assert result["support_levels"] == []


def test_breakout_detected_when_price_closes_above_resistance():
    close = np.concatenate([_oscillating_prices(), np.linspace(102, 112, 5)])

    analysis = analyze_patterns(_as_frame(close))

    assert len(analysis["breakouts"]) == 1
    assert abs(analysis["breakouts"][0]["price_level"] - 105) < 0.01


def test_no_breakout_when_price_stays_in_range():
    analysis = analyze_patterns(_as_frame(_oscillating_prices()))
    assert analysis["breakouts"] == []


def test_breakout_volume_confirmation():
    levels = [{"price": 105.0, "touches": 3, "last_idx": 10}]
    close = np.concatenate([np.full(30, 100.0), [101, 102, 103, 104, 110]])
    quiet = np.full(len(close), 1_000.0)
    surge = quiet.copy()
    surge[-1] = 5_000.0

    assert detect_breakouts(close, levels, quiet)[0]["volume_confirmed"] is False
    assert detect_breakouts(close, levels, surge)[0]["volume_confirmed"] is True


def test_pattern_records_match_database_enum_and_cap_levels():
    close = np.concatenate([_oscillating_prices(), np.linspace(102, 112, 5)])
    records = to_pattern_records(analyze_patterns(_as_frame(close)), max_levels_per_type=1)

    assert {r["pattern_type"] for r in records} == {"support", "resistance", "breakout"}
    assert all(r["price_level"] > 0 and r["trade_date"] for r in records)
    assert sum(r["pattern_type"] == "support" for r in records) == 1


def test_short_frame_yields_no_records():
    assert to_pattern_records(analyze_patterns(_as_frame(np.array([1.0, 2.0])))) == []
