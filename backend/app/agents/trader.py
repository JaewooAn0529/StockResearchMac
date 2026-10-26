"""Trader (the Trader Agent from TradingAgents).

Reads the analyst reports and the full bull/bear debate, and decides BUY/SELL/HOLD.
The decision is captured as structured output — extracting a decision from free text
with a regex leads to misreads on sentences like "might be worth considering a buy...".
"""

from __future__ import annotations

from app.agents.client import ask_json

_SYSTEM = """
You are the trader. Read all four analyst reports and the bull/bear researcher debate,
then make the final decision.

Base it on which side was more convincing in the debate — but pick the side actually
grounded in the data, not the louder one. If the sides are evenly matched or the data is
insufficient, HOLD is the right answer. Don't use HOLD to dodge a conclusion; use it only
when neither side genuinely prevails.

confidence is the strength of the evidence, not the chance of profit. Lower it when the data is incomplete.
rationale is 3-5 sentences. State which arguments you adopted and which you discarded.
key_risks holds the things that would be the reason if this decision turns out wrong.
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
        out.append(f"[Round {r['round']} bull side]\n{r['bull']}")
        out.append(f"[Round {r['round']} bear side]\n{r['bear']}")
    return "\n\n".join(out)


def run_trader(name: str, ticker: str, reports: dict[str, str], rounds: list[dict]) -> dict:
    labels = {
        "fundamentals": "Fundamentals", "news": "News",
        "technical": "Technical", "flow": "Fund flow",
    }
    prompt = "\n\n".join([
        f"Stock: {name} ({ticker})",
        "Analyst reports:\n" + "\n\n".join(f"[{labels[k]}]\n{v}" for k, v in reports.items()),
        "Researcher debate:\n" + _debate_block(rounds),
    ])
    return ask_json(_SYSTEM, prompt, _SCHEMA, max_tokens=800)
