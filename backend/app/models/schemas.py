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
    """증권사 컨센서스 인용 — 자체 분석이 아니므로 source로 출처를 명시한다."""

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
    # 표준 기술지표 — 현재 상태 계산값이지 미래 예측이 아니다
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
    """과거 유사 하락→회복 통계 — 미래 예측이 아니라 과거 사실 조회.

    summary는 반드시 과거형/참고형 문장이어야 한다("~걸렸습니다"). "다음에도
    ~걸릴 것이다" 식으로 바뀌면 안 된다 — 이 문장은 백엔드에서만 만들고
    프론트엔드는 그대로 표시만 한다(표현 규칙이 한 곳에서만 지켜지게).
    """

    ticker: str
    name: str
    current_price: int
    current_return_pct: float
    applicable: bool  # 매수가 대비 하락 중일 때만 True (상승/보합이면 회복 개념 자체가 해당 없음)
    sufficient_sample: bool
    sample_count: int
    unresolved_count: int
    avg_recovery_days: int | None
    median_recovery_days: int | None
    summary: str
    disclaimer: str = HISTORICAL_DISCLAIMER


class EarningsCalendarResponse(BaseModel):
    """실적발표 캘린더 — DART에 예고된 날짜가 없어 법정 제출기한을 계산한 값이다."""

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
    # 리스크 승인 게이트: reject/revise면 BUY/SELL이 HOLD로 강등되고
    # 원래 판단은 original_decision에 남는다
    original_decision: str | None = None
    gate_applied: bool = False


class AgentTiming(BaseModel):
    """어느 단계가 얼마나 걸렸는지 — 감사 추적용."""

    stage: str
    seconds: float


class RiskReview(BaseModel):
    verdict: str
    concern: str
    adjusted_confidence: str


class DecisionRecord(BaseModel):
    """지난 판단 + 그 이후 실제 주가 변화 (사후 기록 조회, 예측 아님)."""

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
    # ready=대조 완료 / pending=판단 당일이라 아직 종가 미확정 / error=조회 실패
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
    # 감사 추적 — 단계별 소요시간과 총 LLM 호출 수
    timings: list[AgentTiming] = []
    total_seconds: float = 0
    llm_calls: int = 0
    created_at: str = ""
    disclaimer: str = DISCLAIMER


class DailySnapshotRow(BaseModel):
    """앱 UI가 아니라 외부 백테스트 스크립트가 쓰는 리서치 전용 스키마.

    daily_log.py가 만들던 스키마와 필드명을 그대로 맞춰서, 이 엔드포인트가
    그 스크립트의 드롭인 대체가 되게 했다.
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
