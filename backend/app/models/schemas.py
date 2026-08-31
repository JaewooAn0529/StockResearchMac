from pydantic import BaseModel

DISCLAIMER = "이 정보는 투자 판단을 돕기 위한 참고 자료이며, 투자 판단과 그 책임은 본인에게 있습니다."
HISTORICAL_DISCLAIMER = "과거 데이터이며 미래 결과를 보장하지 않습니다."


class SearchResult(BaseModel):
    ticker: str
    name: str
    market: str


class OHLCVPoint(BaseModel):
    date: str
    open: int
    high: int
    low: int
    close: int
    volume: int


class PriceResponse(BaseModel):
    ticker: str
    name: str
    current_price: int
    change_pct: float
    as_of_date: str
    ohlcv: list[OHLCVPoint]
    disclaimer: str = DISCLAIMER


class FlowPoint(BaseModel):
    date: str
    foreign_net_buy: int
    institution_net_buy: int


class FlowsResponse(BaseModel):
    ticker: str
    name: str
    series: list[FlowPoint]
    disclaimer: str = DISCLAIMER


class ValuationResponse(BaseModel):
    ticker: str
    name: str
    as_of_date: str
    per: float
    pbr: float
    per_min_1y: float | None
    per_median_1y: float | None
    per_max_1y: float | None
    pbr_min_1y: float | None
    pbr_median_1y: float | None
    pbr_max_1y: float | None
    disclaimer: str = DISCLAIMER


class ConsensusResponse(BaseModel):
    """Brokerage consensus citation — since this isn't original analysis, the source field records where it came from."""

    ticker: str
    name: str
    opinion_score: float
    opinion_text: str | None
    target_price: int
    source: str
    disclaimer: str = DISCLAIMER


class TechnicalResponse(BaseModel):
    ticker: str
    name: str
    as_of_date: str
    close: int
    ma20: float | None
    ma60: float | None
    disparity_20: float | None
    disparity_60: float | None
    volume: int
    avg_volume_20: int | None
    volume_ratio: float | None
    # Standard technical indicators — these are current-state calculated values, not future predictions
    rsi_14: float | None
    macd: float | None
    macd_signal: float | None
    macd_histogram: float | None
    bb_upper: float | None
    bb_middle: float | None
    bb_lower: float | None
    bb_percent_b: float | None
    disclaimer: str = DISCLAIMER


class VolatilityResponse(BaseModel):
    ticker: str
    name: str
    as_of_date: str
    benchmark: str
    window_days: int
    beta: float | None
    annualized_volatility_pct: float
    disclaimer: str = DISCLAIMER


class PeerValuation(BaseModel):
    ticker: str
    name: str
    per: float
    pbr: float


class PeerComparisonResponse(BaseModel):
    ticker: str
    name: str
    industry: str
    peers: list[PeerValuation]
    disclaimer: str = DISCLAIMER


class NewsArticle(BaseModel):
    title: str
    description: str
    published_at: str
    link: str


class NewsResponse(BaseModel):
    ticker: str
    name: str
    articles: list[NewsArticle]
    disclaimer: str = DISCLAIMER


class RecoveryHistoryResponse(BaseModel):
    """Historical decline-to-recovery statistics — a lookup of past facts, not a future prediction.

    summary must always be phrased in the past tense / as reference information
    (e.g. "it took ~ days"). It must never read like "it will take ~ days next time" —
    this sentence is generated only on the backend, and the frontend just displays it
    as-is (so this phrasing rule only needs to be enforced in one place).
    """

    ticker: str
    name: str
    current_price: int
    current_return_pct: float
    applicable: bool  # True only when the price is currently below the purchase price (if it's up or flat, the concept of "recovery" doesn't apply)
    sufficient_sample: bool
    sample_count: int
    unresolved_count: int
    avg_recovery_days: int | None
    median_recovery_days: int | None
    summary: str
    disclaimer: str = HISTORICAL_DISCLAIMER


class EarningsCalendarResponse(BaseModel):
    """Earnings announcement calendar — DART doesn't publish an announced date, so this is a computed statutory filing deadline."""

    ticker: str
    name: str
    report_type: str
    deadline_date: str
    d_day: int
    note: str
    disclaimer: str = DISCLAIMER


class RiskFlag(BaseModel):
    title: str
    date: str
    matched_keyword: str
    url: str


class RiskFlagsResponse(BaseModel):
    ticker: str
    name: str
    flags: list[RiskFlag]
    disclaimer: str = DISCLAIMER


class DebateRound(BaseModel):
    round: int
    bull: str
    bear: str


class TraderDecision(BaseModel):
    decision: str
    confidence: str
    rationale: str
    key_risks: list[str]
    winning_side: str
    # Risk approval gate: a reject/revise verdict downgrades BUY/SELL to HOLD,
    # and the original decision is kept in original_decision
    original_decision: str | None = None
    gate_applied: bool = False


class AgentTiming(BaseModel):
    """How long each stage took — for audit trail purposes."""

    stage: str
    seconds: float


class RiskReview(BaseModel):
    verdict: str
    concern: str
    adjusted_confidence: str


class DecisionRecord(BaseModel):
    """A past decision plus the actual price change since then (a retrospective record, not a prediction)."""

    ticker: str
    name: str
    decided_at: str
    decision: str
    original_decision: str | None = None
    gate_applied: bool = False
    confidence: str | None = None
    rationale: str = ""
    risk_verdict: str | None = None
    price_at_decision: int | None = None
    price_now: int | None = None
    return_pct: float | None = None
    days_elapsed: int | None = None
    # ready=comparison complete / pending=decided today, closing price not yet finalized / error=lookup failed
    status: str = "pending"


class DecisionHistoryResponse(BaseModel):
    records: list[DecisionRecord]
    disclaimer: str = HISTORICAL_DISCLAIMER


class DebateAnalysisResponse(BaseModel):
    ticker: str
    name: str
    analyst_reports: dict[str, str]
    debate_rounds: list[DebateRound]
    decision: TraderDecision
    risk_review: RiskReview
    # Audit trail — per-stage timing and total LLM call count
    timings: list[AgentTiming] = []
    total_seconds: float = 0
    llm_calls: int = 0
    created_at: str = ""
    disclaimer: str = DISCLAIMER


class DailySnapshotRow(BaseModel):
    """A research-only schema used by external backtest scripts, not the app UI.

    Field names deliberately match the schema daily_log.py used to produce, so this
    endpoint can be a drop-in replacement for that script.
    """

    date: str
    ticker: str
    name: str
    rank: int
    foreign_net_buy: int
    close: int
    kospi_close: float | None
    news_count: int | None = None


class DailySnapshotResponse(BaseModel):
    date: str
    market: str
    count: int
    rows: list[DailySnapshotRow]
