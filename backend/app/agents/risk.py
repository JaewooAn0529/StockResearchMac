"""Risk manager (the Risk Management layer from the TradingAgents paper).

Approves or rejects the trader's decision. It looks at the same data as the trader
but plays a different role — not "is this decision right" but "is this decision
survivable." It's kept as a separate layer because having the decision-maker
re-review their own decision tends to just produce self-confirmation.
"""

from __future__ import annotations

from app.agents.client import ask_json

_SYSTEM = """
You are the risk manager. Decide whether to approve or reject the trader's decision.

Your role is not to re-argue the direction of the decision, but to check whether it
overreaches relative to its evidence. Check:
- Is the evidence the trader cited actually in the data, or is it a leap?
- Is the confidence level excessive given volatility, beta, and the 1-day 95% VaR?
- Did the rationale omit a risk that could overturn the decision?

The VaR and the suggested maximum position in the reference data are already computed —
don't estimate new ones. Cite those numbers in concern as actual evidence for your call
(e.g. "VaR is large, so high confidence is excessive").

If the verdict is revise, state concretely in concern what needs to be re-examined.
If the data is sufficient and the logic has no leaps, don't hesitate to approve — rejection
is not the default. Keep concern to 3 sentences or fewer.
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
        f"Stock: {name} ({ticker})",
        "Trader decision:\n"
        f"- Decision: {decision['decision']} (confidence {decision['confidence']})\n"
        f"- Debate winner: {decision['winning_side']}\n"
        f"- Rationale: {decision['rationale']}\n"
        f"- Self-reported risks: {'; '.join(decision['key_risks'])}",
        "Reference data:\n"
        f"{fmt.format_volatility(data.get('volatility'))}\n"
        f"{fmt.format_valuation(data.get('valuation'))}",
    ])
    # 500 was cutting the local model off mid-JSON-string on longer concern
    # text (observed: "Unterminated string" parse failures) — 800 gives it
    # enough room to actually finish the object it started.
    result = ask_json(_SYSTEM, prompt, _SCHEMA, max_tokens=800)

    # The position-size number itself is computed deterministically in
    # volatility.py (from real VaR math), not left to the LLM to invent —
    # the model's job is the qualitative approve/revise/reject call, not
    # arithmetic.
    volatility = data.get("volatility")
    result["suggested_position_pct"] = volatility.get("suggested_max_position_pct") if volatility else None
    return result
