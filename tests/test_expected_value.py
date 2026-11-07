import numpy as np
import pandas as pd
from expected_value import expected_difference, expected_value


def daily(level=1000.0, days=200, seed=1):
    idx = pd.date_range("2026-01-01", periods=days, freq="D")
    noise = np.random.default_rng(seed).normal(1, 0.03, days)
    return pd.Series(level * np.where(idx.day_of_week < 5, 1.2, 0.6) * noise, index=idx)


def test_ordinary_days_stay_inside_the_band():
    s = daily()
    assert (expected_value(s, s.index[-1])["verdict"] == "normal").mean() > 0.9


def test_spike_reads_above():
    s = daily()
    s.iloc[-1] *= 2
    assert expected_value(s, s.index[-1])["verdict"].iloc[-1] == "above"


def test_drop_reads_below():
    s = daily()
    s.iloc[-1] *= 0.4
    assert expected_value(s, s.index[-1])["verdict"].iloc[-1] == "below"


def test_weekday_pattern_is_learned():
    s = daily()
    out = expected_value(s, s.index[-1])
    weekend = out[out.index.day_of_week >= 5]["expected"].mean()
    weekday = out[out.index.day_of_week < 5]["expected"].mean()
    assert weekday / weekend > 1.7


def test_net_flow_band_handles_negative_values():
    cash_in, cash_out = daily(1000.0, seed=1), daily(1100.0, seed=2)
    net = expected_difference(expected_value(cash_in, cash_in.index[-1]), expected_value(cash_out, cash_out.index[-1]))
    assert net["expected"].iloc[-1] < 0
    assert net["low"].iloc[-1] < net["expected"].iloc[-1] < net["high"].iloc[-1]
