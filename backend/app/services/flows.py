"""Foreign/institutional net buying trend (indicator #2, supply-demand trend).

daily_log.py's fetch_foreign_net_buy is built for pulling the "top-N stocks
market-wide on a given day," which doesn't fit a per-stock detail view. Instead,
we use get_market_trading_value_by_date to get a time series of net buying
amounts by investor type (foreign/institutional) for a single stock over a
period. With detail=False (the default), the columns are institution total /
other corporations / individuals / foreign total / overall.
"""

from __future__ import annotations  # the `list[dict] | None` syntax needs Python 3.10+ (this environment runs 3.9)

from datetime import datetime, timedelta, timezone

from pykrx import stock

KST = timezone(timedelta(hours=9))


def get_flows(ticker: str, days: int = 90) -> list[dict] | None:
    end = datetime.now(KST)
    start = end - timedelta(days=days)
    df = stock.get_market_trading_value_by_date(
        start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker
    )
    if df is None or df.empty:
        return None

    return [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "foreign_net_buy": int(row.get("외국인합계", 0)),
            "institution_net_buy": int(row.get("기관합계", 0)),
        }
        for idx, row in df.iterrows()
    ]
