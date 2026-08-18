"""밸류에이션 (지표 #4): 현재 PER/PBR vs 최근 1년 밴드.

pykrx의 get_market_fundamental은 적자 기업 등에서 PER/PBR을 0으로 채워 넣는
경우가 있어(의미 없는 값), 밴드 계산 시 0 이하 값은 제외한다.
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
