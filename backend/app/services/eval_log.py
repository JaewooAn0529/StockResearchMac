"""Record past debate decisions and later compare them against the actual stock price.

⚠️ This does not guarantee predictive performance or claim to foresee the future —
it's a retrospective lookup of "this is what we judged at the time, and this is
how the price moved afterward." It's presented to the user that way as well.

Borrowed from Paperclip's agent evals / feedback loop idea — leave a record of
what the agent judged so it can be reviewed later.

Storage is a single JSON Lines file, sized for a personal tool (no DB needed).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from pykrx import stock

KST = timezone(timedelta(hours=9))
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "decisions.jsonl"


def record_decision(result: dict) -> None:
    """Extract just the decision part from a debate result and append it. Failure here doesn't break the debate response."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        decision = result.get("decision", {})
        entry = {
            "ticker": result.get("ticker"),
            "name": result.get("name"),
            "decided_at": result.get("created_at") or datetime.now(KST).isoformat(timespec="seconds"),
            "decision": decision.get("decision"),
            "original_decision": decision.get("original_decision"),
            "gate_applied": decision.get("gate_applied", False),
            "confidence": decision.get("confidence"),
            "rationale": decision.get("rationale", "")[:400],
            "risk_verdict": result.get("risk_review", {}).get("verdict"),
        }
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[warn] failed to record decision: {exc}")


def _price_on_or_after(ticker: str, target: date) -> tuple[str, int] | None:
    """Closing price on the first trading day on or after the given date. Rolls forward to the next business day if it's a market holiday."""
    df = stock.get_market_ohlcv(
        target.strftime("%Y%m%d"),
        (target + timedelta(days=10)).strftime("%Y%m%d"),
        ticker,
    )
    if df is None or df.empty:
        return None
    return df.index[0].strftime("%Y-%m-%d"), int(df["종가"].iloc[0])


def get_history(limit: int = 30) -> list[dict]:
    """Attach "how the price changed afterward" to each recorded decision and return them newest-first."""
    if not LOG_PATH.exists():
        return []

    entries = []
    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    entries = entries[-limit:][::-1]  # newest first

    today = datetime.now(KST).date()
    for e in entries:
        e["price_at_decision"] = None
        e["price_now"] = None
        e["return_pct"] = None
        e["days_elapsed"] = None
        # On the day of the decision, the closing price isn't out yet so there's
        # nothing to compare against. We report a separate status so the UI can
        # distinguish this from "no data."
        e["status"] = "pending"
        try:
            decided = datetime.fromisoformat(e["decided_at"]).date()
            e["days_elapsed"] = (today - decided).days

            then = _price_on_or_after(e["ticker"], decided)
            # For the current price, scan back a few days to land on the most recent trading day
            now = _price_on_or_after(e["ticker"], today - timedelta(days=7))

            if then and now and then[1]:
                e["price_at_decision"] = then[1]
                e["price_now"] = now[1]
                e["return_pct"] = round((now[1] - then[1]) / then[1] * 100, 2)
                e["status"] = "ready"
            else:
                e["status"] = "pending"  # decision was made today, closing price not settled yet
        except Exception as exc:
            print(f"[warn] failed to compare decision ({e.get('ticker')}): {exc}")
            e["status"] = "error"

    return entries
