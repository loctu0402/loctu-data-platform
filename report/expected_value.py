import numpy as np
import pandas as pd

PAYDAYS = {1, 2, 3, 15, 16}


def _fit(history: pd.Series, window: int):
    level = history.abs().rolling(window, min_periods=7).median()
    ratio = (history / level).replace([np.inf, -np.inf], np.nan).dropna()
    weekday = ratio.groupby(ratio.index.day_of_week).median()
    weekday = weekday / weekday.mean()
    deseason = ratio / ratio.index.day_of_week.map(weekday).to_numpy()
    is_payday = ratio.index.day.isin(list(PAYDAYS))
    payday = float(np.nanmedian(deseason[is_payday]) / np.nanmedian(deseason[~is_payday])) if is_payday.any() else 1.0
    adjusted = history / history.index.day_of_week.map(weekday).to_numpy() / np.where(history.index.day.isin(list(PAYDAYS)), payday, 1.0)
    return float(adjusted.tail(window).median()), weekday, payday


def expected_value(series: pd.Series, as_of, window: int = 28, history_days: int = 120,
                   backtest_days: int = 60, k: float = 3.0, min_band: float = 0.05, warmup_band: float = 0.25) -> pd.DataFrame:
    series = series.asfreq("D").fillna(0.0).astype(float)
    as_of = pd.Timestamp(as_of)
    days = pd.date_range(as_of - pd.Timedelta(days=backtest_days - 1), as_of, freq="D")
    rows = []
    for day in days:
        history = series[(series.index < day) & (series.index >= day - pd.Timedelta(days=history_days))]
        if len(history) < window + 7:
            continue
        level, weekday, payday = _fit(history, window)
        expected = level * weekday.get(day.weekday(), 1.0) * (payday if day.day in PAYDAYS else 1.0)
        rows.append({"date": day, "actual": series.get(day, np.nan), "expected": expected})
    out = pd.DataFrame(rows).set_index("date")
    errors = ((out["actual"] - out["expected"]) / out["expected"].abs()).to_numpy()
    widths = []
    for i in range(len(errors)):
        past = errors[:i][~np.isnan(errors[:i])]
        if len(past) < 14:
            widths.append(warmup_band)
        else:
            widths.append(max(k * 1.4826 * float(np.median(np.abs(past - np.median(past)))), min_band))
    spread = out["expected"].abs() * np.array(widths)
    out["low"] = out["expected"] - spread
    out["high"] = out["expected"] + spread
    out["verdict"] = np.select([out["actual"] > out["high"], out["actual"] < out["low"]], ["above", "below"], "normal")
    return out


def expected_difference(plus: pd.DataFrame, minus: pd.DataFrame, k: float = 3.0) -> pd.DataFrame:
    out = pd.DataFrame({"actual": plus["actual"] - minus["actual"], "expected": plus["expected"] - minus["expected"]})
    errors = (out["actual"] - out["expected"]).to_numpy()
    warmup = 0.25 * float((plus["expected"] + minus["expected"]).mean())
    widths = []
    for i in range(len(errors)):
        past = errors[:i]
        widths.append(warmup if len(past) < 14 else k * 1.4826 * float(np.median(np.abs(past - np.median(past)))))
    out["low"] = out["expected"] - np.array(widths)
    out["high"] = out["expected"] + np.array(widths)
    out["verdict"] = np.select([out["actual"] > out["high"], out["actual"] < out["low"]], ["above", "below"], "normal")
    return out
