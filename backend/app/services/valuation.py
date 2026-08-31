"""Valuation (indicator #4): current PER/PBR vs. the trailing 1-year band.

pykrx's get_market_fundamental sometimes fills in PER/PBR as 0 for things like
loss-making companies (a meaningless value), so we exclude values <= 0 when
computing the band.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pykrx import stock

KST = timezone(timedelta(hours=9))


def get_valuation(ticker: str, days: int = 365) -> dict | None:
    end = datetime.now(KST)
    start = end - timedelta(days=days)
    df = stock.get_market_fundamental(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
    if df is None or df.empty:
        return None

    latest = df.iloc[-1]
    per_series = df["PER"][df["PER"] > 0]
    pbr_series = df["PBR"][df["PBR"] > 0]

    return {
        "as_of_date": df.index[-1].strftime("%Y-%m-%d"),
        "per": float(latest["PER"]),
        "pbr": float(latest["PBR"]),
        "per_min_1y": float(per_series.min()) if not per_series.empty else None,
        "per_median_1y": float(per_series.median()) if not per_series.empty else None,
        "per_max_1y": float(per_series.max()) if not per_series.empty else None,
        "pbr_min_1y": float(pbr_series.min()) if not pbr_series.empty else None,
        "pbr_median_1y": float(pbr_series.median()) if not pbr_series.empty else None,
        "pbr_max_1y": float(pbr_series.max()) if not pbr_series.empty else None,
    }
