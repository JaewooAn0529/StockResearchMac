"""One-off script: seed the universe disk cache via pykrx directly, bypassing
KIND (kind.krx.co.kr), which is currently blocked separately from the rest of
KRX. This is slow (~1 call per ticker for names) so it's meant to be run once,
manually, not from a live request. Once app/services/universe.py has a disk
cache, normal KIND-based refreshes resume on their own 7-day TTL.

Industry is left as None here (KIND normally supplies it) — app/services/universe
.get_peers() already handles a missing industry by returning None, so this
doesn't break anything, it just means the "similar industry" comparison is
unavailable until a real KIND refresh succeeds.
"""

import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from pykrx import stock  # noqa: E402

OUT = Path(__file__).resolve().parent / "data" / "universe_cache.json"


def main():
    entries = []
    for market in ("KOSPI", "KOSDAQ"):
        tickers = stock.get_market_ticker_list(market=market)
        print(f"[info] {market}: {len(tickers)} tickers, fetching names...", flush=True)
        for i, ticker in enumerate(tickers):
            try:
                name = stock.get_market_ticker_name(ticker)
            except Exception as exc:
                print(f"[warn] {ticker} name lookup failed: {exc}")
                continue
            entries.append({"ticker": ticker, "name": name, "market": market, "industry": None})
            if (i + 1) % 200 == 0:
                print(f"[progress] {market} {i + 1}/{len(tickers)}", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"entries": entries, "fetched_at": time.time()}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[done] wrote {len(entries)} entries to {OUT}")


if __name__ == "__main__":
    main()
