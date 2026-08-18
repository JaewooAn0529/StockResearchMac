"""변동성/베타 (지표 #5): 시장 대비 이 종목이 얼마나 출렁이는지.

베타는 종목 일간수익률을 해당 종목이 속한 시장 지수(KOSPI/KOSDAQ) 일간수익률에
회귀했을 때의 기울기(공분산/지수분산). 연율화 변동성은 일간수익률 표준편차에
sqrt(252)를 곱해 연 단위로 환산한 값(%).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
from pykrx import stock

from app.services import universe

KST = timezone(timedelta(hours=9))
_INDEX_TICKER = {"KOSPI": "1001", "KOSDAQ": "2001"}
_TRADING_DAYS_PER_YEAR = 252


def get_volatility_beta(ticker: str, days: int = 180) -> dict | None:
    market = universe.get_market(ticker) or "KOSPI"
    index_ticker = _INDEX_TICKER[market]

    end = datetime.now(KST)
    start = end - timedelta(days=days)
    from_str, to_str = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")

    stock_df = stock.get_market_ohlcv(from_str, to_str, ticker)
    index_df = stock.get_index_ohlcv(from_str, to_str, index_ticker)
    if stock_df is None or index_df is None or stock_df.empty or index_df.empty:
        return None

    stock_ret = stock_df["종가"].pct_change().dropna()
    index_ret = index_df["종가"].pct_change().dropna()
    aligned = pd.concat([stock_ret, index_ret], axis=1, join="inner")
    aligned.columns = ["stock", "index"]
    if len(aligned) < 20:  # 표본이 너무 적으면 베타가 무의미
        return None

    index_var = aligned["index"].var()
    beta = aligned["stock"].cov(aligned["index"]) / index_var if index_var else None
    annualized_volatility_pct = float(aligned["stock"].std() * (_TRADING_DAYS_PER_YEAR ** 0.5) * 100)

    return {
        "as_of_date": stock_df.index[-1].strftime("%Y-%m-%d"),
        "benchmark": market,
        "window_days": len(aligned),
        "beta": round(float(beta), 2) if beta is not None else None,
        "annualized_volatility_pct": round(annualized_volatility_pct, 2),
    }
