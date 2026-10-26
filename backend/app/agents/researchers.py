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
Keep it to 5 sentences or fewer. Cite only evidence actually in the analyst reports; never invent facts.
If the other side's statement is given, open by naming their single weakest argument and rebutting it.
Argue your side honestly — if the other side makes a valid point, concede it and rebuild your case on top of it.
""".strip()

_BULL = (
    "You are the bull-side researcher. Argue the case for buying this stock. "
    f"Your job is to find the upside arguments actually in the data, not baseless optimism.\n\n{_STYLE}"
)

_BEAR = (
    "You are the bear-side researcher. Argue the case for avoiding this stock. "
    f"Your job is to point out the downside risks actually in the data, not vague pessimism.\n\n{_STYLE}"
)


def _reports_block(reports: dict[str, str]) -> str:
    labels = {
        "fundamentals": "Fundamentals analyst",
        "news": "News analyst",
        "technical": "Technical analyst",
        "flow": "Fund-flow analyst",
    }
    return "\n\n".join(f"[{labels[k]}]\n{v}" for k, v in reports.items())


def run_debate(name: str, ticker: str, reports: dict[str, str]) -> list[dict]:
    """Returns per-round statements in the form [{round, bull, bear}, ...]."""
    base = f"Stock: {name} ({ticker})\n\nAnalyst reports:\n{_reports_block(reports)}"
    rounds = []
    bull_last = bear_last = None

    for i in range(1, MAX_DEBATE_ROUNDS + 1):
        bull_prompt = base
        if bear_last:
            bull_prompt += f"\n\nBear side's previous statement:\n{bear_last}"
        bull_last = ask(_BULL, bull_prompt, max_tokens=600)

        # Bear responds after seeing Bull's statement from the same round (a back-and-forth, not simultaneous statements)
        bear_prompt = f"{base}\n\nBull side's previous statement:\n{bull_last}"
        bear_last = ask(_BEAR, bear_prompt, max_tokens=600)

        rounds.append({"round": i, "bull": bull_last, "bear": bear_last})

    return rounds
