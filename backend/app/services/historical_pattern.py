"""Look up historical instances of a similar drop-then-recovery pattern.

⚠️ This is not a future prediction — it's a purely retrospective statistical
lookup. Phrases that assert the future, like "it will likely take this many
days next time too," are forbidden here and in the macOS app that consumes
this data — sentences placed in the summary field must always be phrased in
the past tense / as reference only, e.g. "historically..." or "looking at
past cases...". If there are fewer than 2 samples, we don't emit the
statistics at all (sufficient_sample=False).

Algorithm:
1. For the closing-price time series, compute the daily drawdown against the
   "running high up to that point" (the highest price seen so far).
2. Find past periods where the drawdown was similar (within a tolerance) to
   the user's current drawdown (relative to their purchase price) — consecutive
   matching days are grouped into a single episode (so we don't double-count
   multiple days of the same decline), and only the episode's start date is
   used as a sample.
3. For each episode start date, record the number of days until the closing
   price climbs back above the running high at that time, as the "days to
   recover." Episodes that never recovered before the data ran out are
   excluded from the average (since we can't say for certain they never would
   have recovered — they're incomplete cases).
"""

from __future__ import annotations

import statistics
from datetime import date

from pykrx import stock

_TOLERANCE_PCT = 4.0  # a drawdown within this range is considered a "similar drawdown"
_MIN_SAMPLE = 2


def get_recovery_history(ticker: str, buy_price: float) -> dict | None:
    df = stock.get_market_ohlcv("20000101", date.today().strftime("%Y%m%d"), ticker)
    if df is None or df.empty or len(df) < 30:
        return None

    closes = df["종가"]
    current_price = float(closes.iloc[-1])
    current_return_pct = (current_price - buy_price) / buy_price * 100

    if current_return_pct >= 0:
        return {
            "current_price": int(current_price),
            "current_return_pct": round(current_return_pct, 2),
            "applicable": False,
            "sufficient_sample": False,
            "sample_count": 0,
            "unresolved_count": 0,
            "avg_recovery_days": None,
            "median_recovery_days": None,
            "summary": "The current price is at or above your purchase price, so drawdown-recovery history doesn't apply.",
        }

    running_max = closes.cummax()
    drawdown_pct = (closes - running_max) / running_max * 100

    lower, upper = current_return_pct - _TOLERANCE_PCT, current_return_pct + _TOLERANCE_PCT
    is_match = (drawdown_pct >= lower) & (drawdown_pct <= upper)

    # Group consecutive matching days into a single episode and keep only the
    # start-date index. If we stopped here, a single long decline that dips in
    # and out of the tolerance band every few days would get double-counted as
    # separate cases (confirmed empirically) — so we merge a start date into
    # the previous episode if it falls within 60 days of it.
    _MERGE_GAP_DAYS = 60
    raw_starts: list[int] = []
    in_episode = False
    for i, matched in enumerate(is_match):
        if matched and not in_episode:
            raw_starts.append(i)
            in_episode = True
        elif not matched:
            in_episode = False

    episode_starts: list[int] = []
    for idx in raw_starts:
        if episode_starts and (closes.index[idx] - closes.index[episode_starts[-1]]).days <= _MERGE_GAP_DAYS:
            continue  # treated as the same decline as the previous case — not counted as a new sample
        episode_starts.append(idx)

    recovery_days: list[int] = []
    for start_idx in episode_starts:
        peak_price = running_max.iloc[start_idx]
        future = closes.iloc[start_idx + 1:]
        recovered = future[future >= peak_price]
        if not recovered.empty:
            days = (recovered.index[0] - closes.index[start_idx]).days
            recovery_days.append(days)
        # else: this episode never recovered before the data ended — excluded from the average as incomplete

    sample_count = len(recovery_days)
    unresolved_count = len(episode_starts) - sample_count

    if sample_count < _MIN_SAMPLE:
        return {
            "current_price": int(current_price),
            "current_return_pct": round(current_return_pct, 2),
            "applicable": True,
            "sufficient_sample": False,
            "sample_count": sample_count,
            "unresolved_count": unresolved_count,
            "avg_recovery_days": None,
            "median_recovery_days": None,
            "summary": "There aren't enough past cases to reference.",
        }

    avg_days = round(statistics.mean(recovery_days))
    median_days = round(statistics.median(recovery_days))

    return {
        "current_price": int(current_price),
        "current_return_pct": round(current_return_pct, 2),
        "applicable": True,
        "sufficient_sample": True,
        "sample_count": sample_count,
        "unresolved_count": unresolved_count,
        "avg_recovery_days": avg_days,
        "median_recovery_days": median_days,
        "summary": (
            f"Historically, there were {sample_count} cases where this stock fell by a similar "
            f"amount (about {current_return_pct:.1f}% vs the purchase price) and took an average of "
            f"{avg_days} days (median {median_days}) to recover its previous high."
        ),
    }
