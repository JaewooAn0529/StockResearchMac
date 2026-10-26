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
Write 4-6 sentences. No summary paragraph or repetition — only your judgment and its evidence.
When citing a number, use the value exactly as given in the data, and never estimate a value that isn't there.
If the data is insufficient, say so explicitly.
End with one line: "Stance: Positive / Neutral / Negative".
""".strip()

_ANALYSTS = {
    "fundamentals": (
        "You are a fundamentals analyst. Using only valuation, brokerage consensus, and the "
        "peer comparison, judge whether this stock is expensive or cheap at its current price. "
        "The consensus target price is a citation of brokers' public data, not your own judgment "
        f"— treat it that way.\n\n{_STYLE}"
    ),
    "news": (
        "You are a news analyst. Using only recent headlines and summaries, judge which way "
        "the narrative around this stock is heading. Weigh the substance, not the article count. "
        "Distinguish press-release fluff from material events. The articles are in Korean; "
        f"write your analysis in English.\n\n{_STYLE}"
    ),
    "technical": (
        "You are a technical analyst. Using only moving-average disparity, volume, price trend, "
        "and volatility/beta, judge where the stock is in its current phase. A disparity below 100 "
        f"means below the moving average; above 100 means above it.\n\n{_STYLE}"
    ),
    "flow": (
        "You are a fund-flow analyst. Judge using only the trend in foreign and institutional "
        "net buying. In the Korean market, foreign net buying is often read as a directional "
        "signal, but it also happens for reasons unrelated to the stock, like index rebalancing "
        "or currency hedging — account for that. Look at both the absolute size and the "
        f"persistence of the flows.\n\n{_STYLE}"
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
        prompt = f"Stock: {name} ({ticker})\n\n{_slice(key, data)}"
        # The instruction asks for 4-6 sentences, but if max_tokens is too generous the
        # local model tends to over-generate and the language breaks down toward the end
        # (observed with Qwen2.5), so we keep this tight.
        return key, ask(_ANALYSTS[key], prompt, max_tokens=700)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(one, _ANALYSTS))
