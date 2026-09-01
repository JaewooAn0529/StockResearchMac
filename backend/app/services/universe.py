"""Caching and searching the full KOSPI/KOSDAQ stock master list.

The KRX "all-stock quotes" (MDCSTAT01501) report that pykrx's
get_market_ticker_list()/get_market_ticker_name() depend on is blocked by
anti-bot protection (400 LOGOUT, even when a session cookie is supplied). We
use the listed-company list download from KIND (kind.krx.co.kr), a subsidiary
of the Korea Exchange, instead. This is publicly accessible and even includes
the market classification.
"""

from __future__ import annotations

import io
import json
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd
import requests

_KIND_URL = "http://kind.krx.co.kr/corpgeneral/corpList.do"
_MARKET_MAP = {"유가": "KOSPI", "코스닥": "KOSDAQ"}

# The listed-company list barely changes (a handful of IPOs/delistings a
# year), so we don't need a fresh network call on every backend restart —
# and KRX/KIND occasionally rate-limits or IP-blocks this Mac for hours at a
# time, which used to take search down completely. A disk cache with a
# generous TTL, plus falling back to a stale cache when the network fetch
# fails, means a KRX outage no longer breaks search.
_DISK_CACHE = Path(__file__).resolve().parent.parent.parent / "data" / "universe_cache.json"
_CACHE_TTL = timedelta(days=7)

_cache: list[dict] | None = None
_by_ticker: dict[str, dict] | None = None


def _fetch_from_kind() -> list[dict]:
    res = requests.get(
        _KIND_URL,
        params={"method": "download"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    res.raise_for_status()
    res.encoding = "euc-kr"
    df = pd.read_html(io.StringIO(res.text), header=0)[0]
    df["종목코드"] = df["종목코드"].astype(str).str.zfill(6)

    entries = []
    for _, row in df.iterrows():
        market = _MARKET_MAP.get(row["시장구분"])
        if market is None:  # exclude out-of-scope markets like KONEX
            continue
        entries.append({
            "ticker": row["종목코드"],
            "name": row["회사명"],
            "market": market,
            "industry": row["업종"] if pd.notna(row["업종"]) else None,
        })
    return entries


def _read_disk_cache() -> tuple[list[dict], float] | None:
    if not _DISK_CACHE.exists():
        return None
    try:
        payload = json.loads(_DISK_CACHE.read_text(encoding="utf-8"))
        return payload["entries"], payload["fetched_at"]
    except Exception as exc:
        print(f"[warn] universe disk cache unreadable, ignoring it: {exc}")
        return None


def _write_disk_cache(entries: list[dict]) -> None:
    try:
        _DISK_CACHE.parent.mkdir(parents=True, exist_ok=True)
        _DISK_CACHE.write_text(
            json.dumps({"entries": entries, "fetched_at": time.time()}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"[warn] failed to write universe disk cache: {exc}")


def _build_universe() -> list[dict]:
    disk = _read_disk_cache()
    is_fresh = disk is not None and (time.time() - disk[1]) < _CACHE_TTL.total_seconds()

    if is_fresh:
        return disk[0]

    try:
        entries = _fetch_from_kind()
        _write_disk_cache(entries)
        return entries
    except Exception as exc:
        if disk is not None:
            # KRX/KIND is down or blocking us again — serve the stale cache
            # rather than taking search down entirely.
            age_days = (time.time() - disk[1]) / 86400
            print(f"[warn] KIND fetch failed ({exc}); falling back to disk cache ({age_days:.1f}d old)")
            return disk[0]
        raise  # first-ever run with no cache and no network — nothing to serve


def get_universe() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = _build_universe()
    return _cache


def get_by_ticker(ticker: str) -> dict | None:
    global _by_ticker
    if _by_ticker is None:
        _by_ticker = {e["ticker"]: e for e in get_universe()}
    return _by_ticker.get(ticker)


def get_market(ticker: str) -> str | None:
    entry = get_by_ticker(ticker)
    return entry["market"] if entry else None


def get_peers(ticker: str, limit: int = 5) -> list[dict] | None:
    """Other stocks in the same industry (excluding itself)."""
    entry = get_by_ticker(ticker)
    if entry is None or not entry["industry"]:
        return None
    return [
        e for e in get_universe()
        if e["industry"] == entry["industry"] and e["ticker"] != ticker
    ][:limit]


def search(query: str, limit: int = 20) -> list[dict]:
    q = query.strip()
    if not q:
        return []
    q_upper = q.upper()
    return [
        e for e in get_universe()
        if q in e["name"] or e["ticker"] == q_upper
    ][:limit]
