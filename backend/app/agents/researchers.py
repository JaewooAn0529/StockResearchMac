"""Researcher debate (the Researcher Team from the TradingAgents paper).

Bull and Bear read the same analyst reports and rebut each other. Each round's
prompt includes the opponent's previous statement, so from round 2 onward the
agents focus on tearing down the other's argument rather than making new claims.
Without this rebuttal pressure, the two agents would just each deliver a monologue
and stop.
"""

from __future__ import annotations

from app.agents.client import ask
from app.core.config import MAX_DEBATE_ROUNDS

_STYLE = """
분량은 5문장 이내. 분석가 리포트에 실제로 있는 근거만 인용하고, 없는 사실을 지어내지 않는다.
상대 발언이 주어졌다면 가장 약한 논거 하나를 지목해 반박하는 것으로 시작한다.
자기 입장을 정직하게 변론하되, 상대 지적이 맞으면 인정하고 그 위에서 논지를 다시 세운다.
""".strip()

_BULL = (
    "당신은 매수 측 연구원이다. 이 종목을 사야 할 이유를 변론한다. "
    f"근거 없는 낙관이 아니라 데이터에 있는 상승 논거를 찾아내는 게 역할이다.\n\n{_STYLE}"
)

_BEAR = (
    "당신은 매도 측 연구원이다. 이 종목을 피해야 할 이유를 변론한다. "
    f"막연한 비관이 아니라 데이터에 있는 하방 위험을 짚어내는 게 역할이다.\n\n{_STYLE}"
)


def _reports_block(reports: dict[str, str]) -> str:
    labels = {
        "fundamentals": "펀더멘털 분석가",
        "news": "뉴스 분석가",
        "technical": "기술적 분석가",
        "flow": "수급 분석가",
    }
    return "\n\n".join(f"[{labels[k]}]\n{v}" for k, v in reports.items())


def run_debate(name: str, ticker: str, reports: dict[str, str]) -> list[dict]:
    """Returns per-round statements in the form [{round, bull, bear}, ...]."""
    base = f"종목: {name} ({ticker})\n\n분석가 리포트:\n{_reports_block(reports)}"
    rounds = []
    bull_last = bear_last = None

    for i in range(1, MAX_DEBATE_ROUNDS + 1):
        bull_prompt = base
        if bear_last:
            bull_prompt += f"\n\n매도 측 직전 발언:\n{bear_last}"
        bull_last = ask(_BULL, bull_prompt, max_tokens=600)

        # Bear responds after seeing Bull's statement from the same round (a back-and-forth, not simultaneous statements)
        bear_prompt = f"{base}\n\n매수 측 직전 발언:\n{bull_last}"
        bear_last = ask(_BEAR, bear_prompt, max_tokens=600)

        rounds.append({"round": i, "bull": bull_last, "bear": bear_last})

    return rounds
