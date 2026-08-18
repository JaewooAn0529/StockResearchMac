"""분석가 팀 (TradingAgents의 Analyst Team).

원 논문은 Fundamentals / Sentiment / News / Technical 네 명을 두는데,
Sentiment 분석가는 Reddit·StockTwits 기반이라 한국 시장에 대응물이 없다.
그 자리를 외국인·기관 수급 분석가로 바꿨다 — 한국 시장에서 수급은 미국의
리테일 센티먼트와 비슷한 위치의 신호이고, 조작 가능성이 낮다.

네 명은 서로의 의견을 보지 않는다. 각자 자기 데이터만 보고 독립적으로
판단해야 이후 토론에서 관점이 실제로 갈린다.
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
    """네 분석가를 병렬로 실행한다. 순차 실행하면 응답이 4배 느려진다."""

    def one(key: str) -> tuple[str, str]:
        prompt = f"종목: {name} ({ticker})\n\n{_slice(key, data)}"
        # 4~6문장 지시인데 max_tokens를 너무 크게 주면 로컬 모델이 필요 이상으로
        # 길게 뽑다가 후반부에서 언어가 깨지는 경우가 있어(Qwen2.5 실측) 타이트하게 잡는다
        return key, ask(_ANALYSTS[key], prompt, max_tokens=700)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(one, _ANALYSTS))
