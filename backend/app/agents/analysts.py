"""Analyst team (the Analyst Team from the TradingAgents paper).

The original paper has four analysts: Fundamentals / Sentiment / News / Technical.
The Sentiment analyst is based on Reddit/StockTwits, which has no equivalent in the
Korean market. We replaced that slot with a foreign/institutional flow analyst —
in the Korean market, flow data occupies a signal position similar to U.S. retail
sentiment, and it's harder to manipulate.

The four analysts don't see each other's opinions. Each must judge independently
from only their own data, so that perspectives actually diverge in the debate
that follows.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.agents import formatters as fmt
from app.agents.client import ask

_STYLE = """
분량은 4~6문장. 요약 문단이나 반복은 넣지 말고 판단과 근거만 쓴다.
숫자를 인용할 때는 반드시 주어진 데이터의 값을 그대로 쓰고, 없는 값은 추정하지 않는다.
데이터가 부족하면 부족하다고 명시한다.
마지막 줄에 "관점: 긍정 / 중립 / 부정" 한 줄을 붙인다.
""".strip()

_ANALYSTS = {
    "fundamentals": (
        "당신은 펀더멘털 분석가다. 밸류에이션과 증권사 컨센서스, 동종업계 비교만 보고 "
        "이 종목이 현재 가격에서 비싼지 싼지 판단한다. 컨센서스 목표주가는 당신의 판단이 "
        f"아니라 증권사들의 공개 데이터 인용이므로 그렇게 다룬다.\n\n{_STYLE}"
    ),
    "news": (
        "당신은 뉴스 분석가다. 최근 기사 제목과 요약만 보고 이 종목을 둘러싼 서사가 "
        "어느 방향인지 판단한다. 기사 개수가 아니라 내용의 무게를 본다. 보도자료성 "
        f"기사와 실질적 사건을 구분한다.\n\n{_STYLE}"
    ),
    "technical": (
        "당신은 기술적 분석가다. 이동평균 이격도, 거래량, 가격 추이, 변동성/베타만 보고 "
        "현재 국면이 어디인지 판단한다. 이격도가 100 미만이면 이동평균 아래, 초과면 위다.\n\n"
        f"{_STYLE}"
    ),
    "flow": (
        "당신은 수급 분석가다. 외국인과 기관의 순매수 추이만 보고 판단한다. "
        "한국 시장에서 외국인 순매수는 방향성 신호로 자주 쓰이지만, 지수 리밸런싱이나 "
        "환헤지 같은 종목과 무관한 이유로도 발생한다는 점을 감안한다. "
        f"금액의 절대 규모와 연속성을 함께 본다.\n\n{_STYLE}"
    ),
}


def _slice(name: str, data: dict) -> str:
    price = data.get("price")
    current = price["current_price"] if price else None
    if name == "fundamentals":
        return "\n\n".join([
            fmt.format_valuation(data.get("valuation")),
            fmt.format_consensus(data.get("consensus"), current),
            fmt.format_peers(data.get("peers")),
        ])
    if name == "news":
        return fmt.format_news(data.get("news"))
    if name == "technical":
        return "\n\n".join([
            fmt.format_technical(data.get("technical")),
            fmt.format_volatility(data.get("volatility")),
            fmt.format_price(price),
        ])
    return fmt.format_flows(data.get("flows"))


def run_analysts(name: str, ticker: str, data: dict) -> dict[str, str]:
    """Runs the four analysts in parallel. Running them sequentially would make the response 4x slower."""

    def one(key: str) -> tuple[str, str]:
        prompt = f"종목: {name} ({ticker})\n\n{_slice(key, data)}"
        # The instruction asks for 4-6 sentences, but if max_tokens is too generous the
        # local model tends to over-generate and the language breaks down toward the end
        # (observed with Qwen2.5), so we keep this tight.
        return key, ask(_ANALYSTS[key], prompt, max_tokens=700)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(one, _ANALYSTS))
