"""The full pipeline: data gathering → analysts → debate → trader → risk manager."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from pykrx import stock as krx

from app.agents import client
from app.agents.analysts import run_analysts
from app.agents.researchers import run_debate
from app.agents.risk import run_risk_manager
from app.agents.trader import run_trader
from app.services import consensus as consensus_service
from app.services import flows as flows_service
from app.services import news as news_service
from app.services import peers as peers_service
from app.services import price as price_service
from app.services import technical as technical_service
from app.services import valuation as valuation_service
from app.services import volatility as volatility_service

KST = timezone(timedelta(hours=9))


def gather_data(ticker: str, name: str) -> dict:
    """Gathers 7 data sources in parallel.

    peers alone takes ~9 seconds because it queries 6 stocks sequentially, so running
    everything sequentially would push data gathering past 20 seconds by itself.
    Individual source failures are passed through as None and left for the agent to
    handle as "no data" — there's no reason a single broken source should block the
    whole analysis.
    """
    jobs = {
        "price": lambda: price_service.get_price_and_chart(ticker),
        "flows": lambda: flows_service.get_flows(ticker),
        "valuation": lambda: valuation_service.get_valuation(ticker),
        "consensus": lambda: consensus_service.get_consensus(ticker),
        "technical": lambda: technical_service.get_technical(ticker),
        "volatility": lambda: volatility_service.get_volatility_beta(ticker),
        "peers": lambda: peers_service.get_peer_comparison(ticker),
        "news": lambda: news_service.get_news(name),
    }

    def safe(item):
        key, fn = item
        try:
            return key, fn()
        except Exception as exc:
            print(f"[warn] {key} 수집 실패: {exc}")
            return key, None

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        return dict(pool.map(safe, jobs.items()))


def apply_risk_gate(decision: dict, risk: dict) -> dict:
    """Actually applies the risk manager's verdict to the decision (the approval gate).

    Previously, even if the risk manager rejected a decision, the final decision went
    out unchanged, making the review a formality. Now a reject/revise verdict downgrades
    a trade direction (BUY/SELL) to HOLD — moving only toward the safer side — and the
    original decision is kept in original_decision so the UI can show what was
    overridden and how.
    """
    verdict = (risk.get("verdict") or "").lower()
    original = decision.get("decision")

    gated = dict(decision)
    gated["original_decision"] = original
    gated["gate_applied"] = False

    if verdict in ("reject", "revise") and original in ("BUY", "SELL"):
        gated["decision"] = "HOLD"
        gated["gate_applied"] = True
        concern = risk.get("concern") or "리스크 검토에서 반려됨"
        gated["rationale"] = (
            f"[리스크 검토로 {original} → HOLD 강등] {concern}\n\n"
            f"(원래 트레이더 판단) {decision.get('rationale', '')}"
        )

    # If the risk manager lowered the confidence level, apply that too
    adjusted = risk.get("adjusted_confidence")
    if adjusted:
        gated["confidence"] = adjusted

    return gated


def run_analysis(ticker: str) -> dict:
    name = krx.get_market_ticker_name(ticker)

    client.reset_call_count()
    timings: list[dict] = []
    started = time.monotonic()

    def timed(stage: str, fn):
        t0 = time.monotonic()
        result = fn()
        timings.append({"stage": stage, "seconds": round(time.monotonic() - t0, 1)})
        return result

    data = timed("데이터 수집", lambda: gather_data(ticker, name))
    reports = timed("분석가 4인", lambda: run_analysts(name, ticker, data))
    rounds = timed("연구원 토론", lambda: run_debate(name, ticker, reports))
    decision = timed("트레이더 판단", lambda: run_trader(name, ticker, reports, rounds))
    risk = timed("리스크 검토", lambda: run_risk_manager(name, ticker, decision, data))
    decision = apply_risk_gate(decision, risk)

    return {
        "ticker": ticker,
        "name": name,
        "analyst_reports": reports,
        "debate_rounds": rounds,
        "decision": decision,
        "risk_review": risk,
        "timings": timings,
        "total_seconds": round(time.monotonic() - started, 1),
        "llm_calls": client.get_call_count(),
        "created_at": datetime.now(KST).isoformat(timespec="seconds"),
    }
