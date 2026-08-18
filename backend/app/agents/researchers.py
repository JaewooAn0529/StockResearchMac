"""연구원 토론 (TradingAgents의 Researcher Team).

Bull과 Bear가 같은 분석가 리포트를 보고 서로 반박한다. 라운드마다 상대의
직전 발언이 프롬프트에 들어가므로, 2라운드부터는 새 주장을 펴는 게 아니라
상대 논거를 깨는 데 집중하게 된다. 이 반박 압력이 없으면 두 에이전트가
각자 독백만 하고 끝난다.
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
    """[{round, bull, bear}, ...] 형태로 라운드별 발언을 반환한다."""
    base = f"종목: {name} ({ticker})\n\n분석가 리포트:\n{_reports_block(reports)}"
    rounds = []
    bull_last = bear_last = None

    for i in range(1, MAX_DEBATE_ROUNDS + 1):
        bull_prompt = base
        if bear_last:
            bull_prompt += f"\n\n매도 측 직전 발언:\n{bear_last}"
        bull_last = ask(_BULL, bull_prompt, max_tokens=600)

        # Bear는 같은 라운드의 Bull 발언까지 보고 답한다 (동시 발언이 아니라 응수 구조)
        bear_prompt = f"{base}\n\n매수 측 직전 발언:\n{bull_last}"
        bear_last = ask(_BEAR, bear_prompt, max_tokens=600)

        rounds.append({"round": i, "bull": bull_last, "bear": bear_last})

    return rounds
