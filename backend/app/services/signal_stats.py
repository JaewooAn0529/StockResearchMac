"""Statistical significance of a technical signal (RSI oversold) using past data.

⚠️ Same principle as historical_pattern.py: this is a retrospective lookup,
not a forecast. Most individual stocks only have a handful of RSI<30 episodes
over 10 years — nowhere near enough for a reliable p-value. Rather than
force one out, this reports the sample size plainly and marks the result as
not statistically significant when the sample is too thin. A p-value that's
always < 0.05 regardless of the input would be a red flag, not a feature.

Method: mark each day RSI first drops below the threshold as a "signal day"
(consecutive days below threshold are one episode, not one each — same
reasoning as historical_pattern.py's episode merge). For each signal day,
compute the forward return over `window_days` trading days. Compare that
conditional return distribution against the unconditional distribution of
all `window_days` forward returns over the same history, using Welch's
t-test (unequal variances assumed — safer default than Student's t when we
don't know the two groups have equal variance, and here they usually don't).
That tests "is the return distribution after this signal actually different
from the stock's normal behavior," rather than testing an arbitrary fixed
threshold.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from pykrx import stock
from scipy import stats

_MIN_SAMPLE_FOR_TEST = 2       # can't run a t-test at all below this
_MIN_SAMPLE_FOR_CONFIDENCE = 8  # below this, a t-test can run but isn't trustworthy


def _rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(100)  # no downside days at all -> RSI 100, not undefined


def get_rsi_signal_stats(
    ticker: str,
    window_days: int = 10,
    gain_threshold_pct: float = 5.0,
    rsi_threshold: float = 30.0,
) -> dict | None:
    df = stock.get_market_ohlcv("20160101", date.today().strftime("%Y%m%d"), ticker)
    if df is None or df.empty or len(df) < 60:
        return None

    close = df["종가"]
    rsi = _rsi_series(close)
    fwd_return_pct = (close.shift(-window_days) / close - 1) * 100

    below = rsi < rsi_threshold
    episode_start = below & ~below.shift(1, fill_value=False)

    signal_returns = fwd_return_pct[episode_start].dropna()
    all_returns = fwd_return_pct.dropna()
    n = len(signal_returns)

    base = {
        "as_of_date": df.index[-1].strftime("%Y-%m-%d"),
        "rsi_threshold": rsi_threshold,
        "window_days": window_days,
        "gain_threshold_pct": gain_threshold_pct,
        "sample_count": n,
    }

    if n < _MIN_SAMPLE_FOR_TEST:
        return {
            **base,
            "sufficient_sample": False,
            "statistically_significant": False,
            "hit_rate_pct": None,
            "mean_signal_return_pct": None,
            "mean_baseline_return_pct": None,
            "t_statistic": None,
            "p_value": None,
            "summary": (
                f"In the past data, RSI fell below {rsi_threshold:g} only {n} time(s) — "
                f"below the minimum sample needed for any statistical analysis."
            ),
        }

    hit_rate_pct = float((signal_returns >= gain_threshold_pct).mean() * 100)
    mean_signal = float(signal_returns.mean())
    mean_baseline = float(all_returns.mean())

    # Welch's t-test: does the mean forward return after the signal differ
    # from the stock's unconditional mean forward return?
    t_stat, p_value = stats.ttest_ind(signal_returns, all_returns, equal_var=False)
    sufficient = n >= _MIN_SAMPLE_FOR_CONFIDENCE
    significant = bool(sufficient and p_value < 0.05)

    if not sufficient:
        summary = (
            f"There were {n} past cases of RSI dropping below {rsi_threshold:g} — too few for a "
            f"reliable statistical test. For reference only, {hit_rate_pct:.0f}% of them rose "
            f"{gain_threshold_pct:g}%+ within {window_days} trading days (p={p_value:.3f}), but the "
            f"sample size means this can't be called statistically significant."
        )
    elif significant:
        direction = "higher" if mean_signal > mean_baseline else "lower"
        summary = (
            f"Across {n} past cases of RSI dropping below {rsi_threshold:g}, the average return over "
            f"the next {window_days} trading days was {mean_signal:+.1f}%, statistically significantly "
            f"{direction} than this stock's usual {window_days}-day average ({mean_baseline:+.1f}%) "
            f"(p={p_value:.3f} < 0.05)."
        )
    else:
        summary = (
            f"Across {n} past cases of RSI dropping below {rsi_threshold:g}, the return over the next "
            f"{window_days} trading days (average {mean_signal:+.1f}%) was not statistically "
            f"significantly different from this stock's usual return ({mean_baseline:+.1f}%) "
            f"(p={p_value:.3f})."
        )

    return {
        **base,
        "sufficient_sample": sufficient,
        "statistically_significant": significant,
        "hit_rate_pct": round(hit_rate_pct, 1),
        "mean_signal_return_pct": round(mean_signal, 2),
        "mean_baseline_return_pct": round(mean_baseline, 2),
        "t_statistic": round(float(t_stat), 3),
        "p_value": round(float(p_value), 4),
        "summary": summary,
    }
