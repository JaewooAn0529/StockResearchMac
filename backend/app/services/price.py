"""시세 + 차트. stock-briefing/briefing.py의 get_price 패턴을 확장한 버전.

기존 get_price는 최신가/등락률만 반환했는데, 여기서는 차트용으로 기간 전체
OHLCV 시계열도 함께 반환한다.
"""

from __future__ import annotations  # dict | None 문법은 Python 3.10+ 필요 (이 환경은 3.9)

from datetime import datetime, timedelta, timezone

from pykrx import stock

KST = timezone(timedelta(hours=9))


def get_price_and_chart(ticker: str, days: int = 90) -> dict | None:
    end = datetime.now(KST)
    start = end - timedelta(days=days)
    df = stock.get_market_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
    if df is None or df.empty or len(df) < 2:
        return None

    latest, prev = df.iloc[-1], df.iloc[-2]
    close = int(latest["종가"])
    pct = (close - prev["종가"]) / prev["종가"] * 100

    ohlcv = [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "open": int(row["시가"]),
            "high": int(row["고가"]),
            "low": int(row["저가"]),
            "close": int(row["종가"]),
            "volume": int(row["거래량"]),
        }
        for idx, row in df.iterrows()
    ]

    return {
        "current_price": close,
        "change_pct": round(pct, 2),
        "as_of_date": df.index[-1].strftime("%Y-%m-%d"),
        "ohlcv": ohlcv,
    }
