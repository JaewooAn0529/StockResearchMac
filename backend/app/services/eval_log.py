"""지난 토론 판단을 기록하고 나중에 실제 주가와 대조한다.

⚠️ 이건 예측 성능을 보장하거나 미래를 맞히는 기능이 아니라, "그때 이렇게
판단했고 이후 주가는 이렇게 움직였다"는 사후 기록 조회다. 화면에도 그렇게만
표시한다.

Paperclip의 agent evals / feedback loop 아이디어를 가져온 것 — 에이전트가
낸 판단을 남겨두고 나중에 되돌아볼 수 있게 한다.

저장은 개인용 도구 규모에 맞춰 JSON Lines 한 파일로 한다(DB 불필요).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from pykrx import stock

KST = timezone(timedelta(hours=9))
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "decisions.jsonl"


def record_decision(result: dict) -> None:
    """토론 결과에서 판단 부분만 뽑아 append한다. 실패해도 토론 응답은 살린다."""
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
        print(f"[warn] 판단 기록 실패: {exc}")


def _price_on_or_after(ticker: str, target: date) -> tuple[str, int] | None:
    """해당 날짜 이후 첫 거래일의 종가. 휴장일이면 다음 영업일로 밀린다."""
    df = stock.get_market_ohlcv(
        target.strftime("%Y%m%d"),
        (target + timedelta(days=10)).strftime("%Y%m%d"),
        ticker,
    )
    if df is None or df.empty:
        return None
    return df.index[0].strftime("%Y-%m-%d"), int(df["종가"].iloc[0])


def get_history(limit: int = 30) -> list[dict]:
    """기록된 판단들에 "그 이후 주가 변화"를 붙여서 최신순으로 돌려준다."""
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

    entries = entries[-limit:][::-1]  # 최신순

    today = datetime.now(KST).date()
    for e in entries:
        e["price_at_decision"] = None
        e["price_now"] = None
        e["return_pct"] = None
        e["days_elapsed"] = None
        # 판단 당일에는 아직 종가가 안 나와서 대조할 게 없다. 이걸 화면에서
        # "데이터 없음"과 구분해 안내하려고 상태를 따로 내려준다.
        e["status"] = "pending"
        try:
            decided = datetime.fromisoformat(e["decided_at"]).date()
            e["days_elapsed"] = (today - decided).days

            then = _price_on_or_after(e["ticker"], decided)
            # 최근 종가는 며칠 전부터 훑어서 가장 마지막 거래일을 잡는다
            now = _price_on_or_after(e["ticker"], today - timedelta(days=7))

            if then and now and then[1]:
                e["price_at_decision"] = then[1]
                e["price_now"] = now[1]
                e["return_pct"] = round((now[1] - then[1]) / then[1] * 100, 2)
                e["status"] = "ready"
            else:
                e["status"] = "pending"  # 판단 당일이라 아직 종가 미확정
        except Exception as exc:
            print(f"[warn] 판단 대조 실패 ({e.get('ticker')}): {exc}")
            e["status"] = "error"

    return entries
