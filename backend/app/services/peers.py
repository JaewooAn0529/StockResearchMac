"""동종업계 비교 (지표 #8): 같은 업종 종목들과 PER/PBR 나란히 비교.

업종 분류는 KIND 상장법인목록의 "업종" 컬럼을 그대로 쓴다(KRX 공식 업종
중분류가 아니라 KIND가 부여한 표시용 업종명이라, 세분류가 정교하진 않지만
동종업계 대략적인 비교에는 충분하다).
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

    if len(rows) < 2:  # 비교 대상이 자기 자신뿐이면 의미 없음
        return None

    return {"industry": entry["industry"], "peers": rows}
