"""리스크 매니저 (TradingAgents의 Risk Management 층).

트레이더 결정을 승인/반려한다. 트레이더와 같은 데이터를 보지만 역할이 다르다 —
"이 결정이 맞는가"가 아니라 "이 결정이 감당 가능한가"를 본다. 별도 층으로 두는
이유는, 결정자 자신에게 자기 결정을 재검토시키면 대체로 자기 확증에 그치기 때문이다.
"""

from __future__ import annotations

from app.agents.client import ask_json

_SYSTEM = """
당신은 리스크 매니저다. 트레이더의 결정을 승인할지 반려할지 판단한다.

당신의 역할은 결정의 방향을 다시 논하는 게 아니라, 그 결정이 근거에 비해 과하지
않은지를 보는 것이다. 다음을 확인한다.
- 트레이더가 인용한 근거가 실제 데이터에 있는가, 아니면 비약인가
- 변동성과 베타에 비해 확신 수준이 과한가
- 결정을 뒤집을 만한 위험이 rationale에서 누락됐는가

verdict가 revise면 concern에 무엇을 다시 봐야 하는지 구체적으로 쓴다.
데이터가 충분하고 논리에 비약이 없으면 approve를 주저하지 않는다 — 반려가 기본값은 아니다.
concern은 3문장 이내.
""".strip()

_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["approve", "revise", "reject"]},
        "concern": {"type": "string"},
        "adjusted_confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["verdict", "concern", "adjusted_confidence"],
    "additionalProperties": False,
}


def run_risk_manager(name: str, ticker: str, decision: dict, data: dict) -> dict:
    from app.agents import formatters as fmt

    prompt = "\n\n".join([
        f"종목: {name} ({ticker})",
        "트레이더 결정:\n"
        f"- 판단: {decision['decision']} (확신도 {decision['confidence']})\n"
        f"- 토론 우세: {decision['winning_side']}\n"
        f"- 근거: {decision['rationale']}\n"
        f"- 스스로 밝힌 위험: {'; '.join(decision['key_risks'])}",
        "참고 데이터:\n"
        f"{fmt.format_volatility(data.get('volatility'))}\n"
        f"{fmt.format_valuation(data.get('valuation'))}",
    ])
    return ask_json(_SYSTEM, prompt, _SCHEMA, max_tokens=500)
