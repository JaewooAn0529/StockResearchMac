"""Research-only bulk lookup (meant for backtesting/external scripts, not the app UI).

/stocks/{ticker}/flows gives a time series for one stock over a period; this
does the opposite — for a given "day," it ranks every stock in the market by
foreign net buying. Calling per-stock would mean, for a 3-year backfill,
847 KOSPI stocks x 750 trading days = hundreds of thousands of calls, which
is impractical — so we use pykrx's market-wide bulk functions instead
(3 calls per day).
"""

from __future__ import annotations

import contextlib
import io
from datetime import datetime, timedelta, timezone

from pykrx import stock

from app.services import news as news_service

KST = timezone(timedelta(hours=9))

_INDEX_CODE = {"KOSPI": "1001", "KOSDAQ": "2001"}


class UpstreamFetchError(RuntimeError):
    """Data couldn't be fetched due to a KRX response failure (e.g. rate limiting). Distinct from a market holiday.

    pykrx internally swallows parsing failures like json.JSONDecodeError,
    prints "Error occurred in ..." to stdout, and then returns an empty
    DataFrame (see dataframe_empty_handler in
    site-packages/pykrx/website/comm/util.py). So on the surface it just looks
    like "empty data," indistinguishable from a market holiday — but for
    something that calls repeatedly, like a backfill, these two must never be
    treated as the same thing. A holiday should be skipped, but a rate limit
    should be retried; if we record a rate limit as a "holiday," the data ends
    up silently missing while looking complete.
    """


@contextlib.contextmanager
def _detect_upstream_errors():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield
    if "Error occurred in" in buf.getvalue():
        raise UpstreamFetchError(buf.getvalue().strip())


def _same_day_news_count(name: str, date_str: str) -> int | None:
    """Same concept as daily_log.py's fetch_news_counts — number of articles published on the given day.

    The stock-briefing original called the Naver API directly, but here we
    reuse news_service.get_news, which already has the same filtering
    (whether the stock name appears in the title). This costs one API call
    per stock, so it's recommended to only enable it when the count has
    already been limited via top_n.
    """
    target = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    try:
        articles = news_service.get_news(name, limit=100)
    except Exception as exc:
        print(f"[warn] news lookup failed for {name}: {exc}")
        return None
    return sum(1 for a in articles if a["published_at"].startswith(target))


def get_daily_snapshot(
    date_str: str,
    market: str = "KOSPI",
    top_n: int | None = None,
    include_news: bool = False,
) -> dict | None:
    """date_str: YYYYMMDD. Returns None if it's a market holiday.

    top_n: set this if you only want the top N, as in daily_log.py (the default returns every stock).
    include_news: if True, fills in the day's news count, but only for the
    stocks left after filtering by top_n (this costs one API call per stock,
    so applying it to every stock would be slow and burn through the quota
    quickly).
    """
    if market not in _INDEX_CODE:
        raise ValueError(f"Unsupported market: {market} (KOSPI/KOSDAQ only)")

    with _detect_upstream_errors():
        flow = stock.get_market_net_purchases_of_equities_by_ticker(date_str, date_str, market, "외국인")
    if flow is None or flow.empty:
        return None  # a genuine market holiday — we only reach here when it was empty data with no error

    with _detect_upstream_errors():
        price = stock.get_market_ohlcv(date_str, market=market)
    with _detect_upstream_errors():
        index = stock.get_index_ohlcv(date_str, date_str, _INDEX_CODE[market])
    kospi_close = float(index["종가"].iloc[0]) if index is not None and not index.empty else None

    merged = flow.join(price[["종가"]], how="inner")
    merged = merged.sort_values("순매수거래대금", ascending=False)
    if top_n is not None:
        merged = merged.head(top_n)

    rows = []
    for rank, (ticker, row) in enumerate(merged.iterrows(), start=1):
        name = row["종목명"]
        rows.append({
            "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
            "ticker": ticker,
            "name": name,
            "rank": rank,
            "foreign_net_buy": int(row["순매수거래대금"]),
            "close": int(row["종가"]),
            # The field name is fixed as kospi_close to match daily_log.py's schema.
            # When called with market=KOSDAQ, this value holds the KOSDAQ index close instead.
            "kospi_close": kospi_close,
            "news_count": _same_day_news_count(name, date_str) if include_news else None,
        })

    return {
        "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
        "market": market,
        "count": len(rows),
        "rows": rows,
    }
