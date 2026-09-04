"""Volatility/beta (indicator #5): how much this stock swings relative to the market.

Beta is the slope from regressing the stock's daily returns against the daily
returns of the market index it belongs to (KOSPI/KOSDAQ) — i.e. covariance
divided by index variance. Annualized volatility is the standard deviation of
daily returns multiplied by sqrt(252), converted to a yearly value (%).

Also computes 1-day 95% Value at Risk two ways:
- Parametric (Gaussian): z_0.95 * daily_std. Fast, but assumes returns are
  normally distributed, which understates real tail risk — stock returns are
  fat-tailed in practice.
- Historical: the empirical 5th percentile of actual daily returns. No
  distributional assumption, so it's the more defensible of the two, but
  needs enough history to have real observations out in the tail.
Both are shown so the parametric/historical gap itself is visible rather
than picking one silently.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from pykrx import stock

from app.services import universe

KST = timezone(timedelta(hours=9))
_INDEX_TICKER = {"KOSPI": "1001", "KOSDAQ": "2001"}
_TRADING_DAYS_PER_YEAR = 252
_Z_95 = 1.645  # one-tailed 95% z-score for parametric VaR

# Position-sizing guideline: cap any single position so its own 1-day 95% VaR
# doesn't exceed this share of total portfolio value. 2% is a common desk
# convention for a single-position daily risk budget, not a magic number —
# it's a clearly-labeled assumption the risk manager's guidance is built on.
_DAILY_VAR_BUDGET_PCT = 2.0


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
    if len(aligned) < 20:  # too few samples makes beta meaningless
        return None

    index_var = aligned["index"].var()
    beta = aligned["stock"].cov(aligned["index"]) / index_var if index_var else None
    annualized_volatility_pct = float(aligned["stock"].std() * (_TRADING_DAYS_PER_YEAR ** 0.5) * 100)

    daily_returns = aligned["stock"]
    var_95_parametric_pct = float(_Z_95 * daily_returns.std() * 100)
    var_95_historical_pct = float(-np.percentile(daily_returns, 5) * 100)
    # A position's own VaR shouldn't eat more than the fixed daily risk budget —
    # more volatile stocks get told to take a smaller slice of the portfolio.
    suggested_max_position_pct = round(
        min(100.0, _DAILY_VAR_BUDGET_PCT / var_95_historical_pct * 100) if var_95_historical_pct > 0 else 100.0,
        1,
    )

    return {
        "as_of_date": stock_df.index[-1].strftime("%Y-%m-%d"),
        "benchmark": market,
        "window_days": len(aligned),
        "beta": round(float(beta), 2) if beta is not None else None,
        "annualized_volatility_pct": round(annualized_volatility_pct, 2),
        "var_95_1day_pct": round(var_95_parametric_pct, 2),
        "var_95_1day_historical_pct": round(var_95_historical_pct, 2),
        "suggested_max_position_pct": suggested_max_position_pct,
    }
