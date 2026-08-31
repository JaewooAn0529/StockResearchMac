"""Peer comparison (indicator #8): compares PER/PBR side by side against stocks in the same industry.

Industry classification uses the "industry" column from KIND's listed-company
list as-is (this is a display-oriented industry label assigned by KIND, not
the official KRX industry sub-classification, so it isn't finely granular —
but it's good enough for a rough peer comparison).
"""

from __future__ import annotations

from app.services import universe
from app.services import valuation as valuation_service


def get_peer_comparison(ticker: str, limit: int = 5) -> dict | None:
    entry = universe.get_by_ticker(ticker)
    if entry is None or not entry["industry"]:
        return None

    peer_entries = universe.get_peers(ticker, limit=limit)
    if not peer_entries:
        return None

    rows = []
    self_val = valuation_service.get_valuation(ticker)
    if self_val:
        rows.append({
            "ticker": ticker, "name": entry["name"],
            "per": self_val["per"], "pbr": self_val["pbr"],
        })
    for peer in peer_entries:
        v = valuation_service.get_valuation(peer["ticker"])
        if v:
            rows.append({
                "ticker": peer["ticker"], "name": peer["name"],
                "per": v["per"], "pbr": v["pbr"],
            })

    if len(rows) < 2:  # meaningless if the only entry is the stock itself
        return None

    return {"industry": entry["industry"], "peers": rows}
