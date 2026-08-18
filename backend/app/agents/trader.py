"""트레이더 (TradingAgents의 Trader Agent).

분석가 리포트와 bull/bear 토론 전체를 읽고 BUY/SELL/HOLD를 결정한다.
결정은 구조화 출력으로 받는다 — 자유 서술에서 결정을 정규식으로 뽑아내면
"매수를 고려해볼 만하지만..." 같은 문장에서 오판이 난다.
"""

from __future__ import annotations

from app.agents.client import ask_json

_SYSTEM = """
당신은 트레이더다. 분석가 네 명의 리포트와 매수/매도 연구원의 토론을 모두 읽고
최종 결정을 내린다.

토론에서 어느 쪽이 더 설득력 있었는지를 판단 근거로 삼되, 목소리가 큰 쪽이 아니라
데이터에 실제로 근거한 쪽을 택한다. 양측이 팽팽하거나 데이터가 부족하면 HOLD가 정답이다.
HOLD를 결론 회피용으로 쓰지는 말고, 실제로 어느 쪽도 우세하지 않을 때만 쓴다.

confidence는 근거의 강도이지 수익 가능성이 아니다. 데이터가 불완전하면 낮춘다.
rationale은 3~5문장. 어떤 논거를 채택하고 어떤 논거를 버렸는지 밝힌다.
key_risks에는 이 결정이 틀렸다면 그 이유가 될 만한 것을 담는다.
""".strip()

_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "rationale": {"type": "string"},
        "key_risks": {"type": "array", "items": {"type": "string"}},
        "winning_side": {"type": "string", "enum": ["bull", "bear", "neither"]},
    },
    "required": ["decision", "confidence", "rationale", "key_risks", "winning_side"],
    "additionalProperties": False,
}


def _debate_block(rounds: list[dict]) -> str:
    out = []
    for r in rounds:
        out.append(f"[{r['round']}라운드 매수 측]\n{r['bull']}")
        out.append(f"[{r['round']}라운드 매도 측]\n{r['bear']}")
    return "\n\n".join(out)


def run_trader(name: str, ticker: str, reports: dict[str, str], rounds: list[dict]) -> dict:
    labels = {
        "fundamentals": "펀더멘털", "news": "뉴스",
        "technical": "기술적", "flow": "수급",
    }
    prompt = "\n\n".join([
        f"종목: {name} ({ticker})",
        "분석가 리포트:\n" + "\n\n".join(f"[{labels[k]}]\n{v}" for k, v in reports.items()),
        "연구원 토론:\n" + _debate_block(rounds),
    ])
    return ask_json(_SYSTEM, prompt, _SCHEMA, max_tokens=800)
