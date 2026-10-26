"""Compresses raw data so it can fit into a prompt.

Feeding in 62 trading days of raw OHLCV and flow time series as-is would just burn
tokens without the model actually reading it. We keep only the aggregated values
the agent actually uses to make its judgment.
"""

from __future__ import annotations


def _man(won: float) -> str:
    """Converts a won amount to KRW billions. Flow amounts can reach into the trillions, and left as-is they're hard to read."""
    return f"₩{won / 1e9:,.1f}B"


def format_price(price: dict | None) -> str:
    if not price:
        return "No price data"
    ohlcv = price["ohlcv"]
    closes = [p["close"] for p in ohlcv]
    recent = ohlcv[-20:]
    lines = [
        f"Current price ₩{price['current_price']:,} ({price['change_pct']:+.2f}%, as of {price['as_of_date']})",
        f"Over the period ({len(ohlcv)} trading days): high ₩{max(closes):,} / low ₩{min(closes):,}",
        "Closing prices, last 20 trading days:",
    ]
    lines += [f"  {p['date']} ₩{p['close']:,} (volume {p['volume']:,})" for p in recent]
    return "\n".join(lines)


def format_flows(flows: list[dict] | None) -> str:
    if not flows:
        return "No fund-flow data"

    def cum(days: int, key: str) -> float:
        return sum(p[key] for p in flows[-days:])

    lines = ["Cumulative foreign/institutional net buying (positive = net buy, negative = net sell):"]
    for days in (5, 20, 60):
        if len(flows) >= days:
            lines.append(
                f"  Last {days} trading days: foreign {_man(cum(days, 'foreign_net_buy'))}, "
                f"institutional {_man(cum(days, 'institution_net_buy'))}"
            )
    lines.append("Daily, last 10 trading days:")
    for p in flows[-10:]:
        lines.append(
            f"  {p['date']} foreign {_man(p['foreign_net_buy'])} / institutional {_man(p['institution_net_buy'])}"
        )
    return "\n".join(lines)


def format_valuation(v: dict | None) -> str:
    if not v:
        return "No valuation data"
    return "\n".join([
        f"Current PER {v['per']} / PBR {v['pbr']} (as of {v['as_of_date']})",
        f"1-year PER band: low {v['per_min_1y']} / median {v['per_median_1y']} / high {v['per_max_1y']}",
        f"1-year PBR band: low {v['pbr_min_1y']} / median {v['pbr_median_1y']} / high {v['pbr_max_1y']}",
    ])


def format_consensus(c: dict | None, current_price: int | None) -> str:
    if not c:
        return "No brokerage consensus (insufficient coverage)"
    line = f"Brokerage consensus rating {c['opinion_score']} ({c['opinion_text']}), target price ₩{c['target_price']:,}"
    if current_price:
        gap = (c["target_price"] - current_price) / current_price * 100
        line += f" — {gap:+.1f}% vs current price"
    return f"{line}\nSource: {c['source']} (cited data, not our own analysis)"


def format_technical(t: dict | None) -> str:
    if not t:
        return "No technical indicator data"
    lines = [
        f"Close ₩{t['close']:,} (as of {t['as_of_date']})",
        f"20-day moving average ₩{t['ma20']:,.0f} / disparity {t['disparity_20']}%",
        f"60-day moving average ₩{t['ma60']:,.0f} / disparity {t['disparity_60']}%",
        f"Today's volume {t['volume']:,} / {t['volume_ratio']}x the 20-day average",
    ]
    # Standard indicators are only included when a value exists (None if the sample is too short)
    if t.get("rsi_14") is not None:
        lines.append(f"RSI(14) {t['rsi_14']} (conventionally 70+ = overbought / 30- = oversold)")
    if t.get("macd") is not None:
        lines.append(
            f"MACD {t['macd']} / signal {t['macd_signal']} / histogram {t['macd_histogram']}"
        )
    if t.get("bb_upper") is not None:
        lines.append(
            f"Bollinger Bands upper {t['bb_upper']:,.0f} / middle {t['bb_middle']:,.0f} / "
            f"lower {t['bb_lower']:,.0f} / %B {t['bb_percent_b']}"
        )
    return "\n".join(lines)


def format_volatility(v: dict | None) -> str:
    if not v:
        return "No volatility data"
    return (
        f"Beta {v['beta']} (vs the {v['benchmark']} index, {v['window_days']}-trading-day sample) / "
        f"annualized volatility {v['annualized_volatility_pct']}%\n"
        f"1-day 95% VaR: normal-distribution {v['var_95_1day_pct']}% / historical 5th percentile {v['var_95_1day_historical_pct']}% "
        f"(estimated worst one-day loss; the historical figure is more reliable)\n"
        f"Suggested max position: to keep this stock's VaR within a 2% daily risk budget, cap it at "
        f"{v['suggested_max_position_pct']}% of the portfolio"
    )


def format_peers(p: dict | None) -> str:
    if not p:
        return "No peer comparison data"
    lines = [f"Industry: {p['industry']}"]
    lines += [f"  {r['name']}({r['ticker']}) PER {r['per']} / PBR {r['pbr']}" for r in p["peers"]]
    return "\n".join(lines)


def format_news(news: list[dict] | None) -> str:
    if not news:
        return "No news collected (Naver API key not set, or no related articles)"
    return "\n".join(
        f"[{n['published_at']}] {n['title']}\n  {n['description']}" for n in news
    )
