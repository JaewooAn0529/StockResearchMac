import Foundation

// 백엔드 app/models/schemas.py 1:1 대응. 필드명은 snake_case 그대로 두고
// APIClient의 JSONDecoder에서 .convertFromSnakeCase로 일괄 변환한다.

struct SearchResult: Codable, Identifiable, Hashable {
    var id: String { ticker }
    let ticker: String
    let name: String
    let market: String
}

struct OHLCVPoint: Codable, Identifiable {
    var id: String { date }
    let date: String
    let open: Int
    let high: Int
    let low: Int
    let close: Int
    let volume: Int
}

struct PriceResponse: Codable {
    let ticker: String
    let name: String
    let currentPrice: Int
    let changePct: Double
    let asOfDate: String
    let ohlcv: [OHLCVPoint]
    let disclaimer: String
}

struct FlowPoint: Codable, Identifiable {
    var id: String { date }
    let date: String
    let foreignNetBuy: Int
    let institutionNetBuy: Int
}

struct FlowsResponse: Codable {
    let ticker: String
    let name: String
    let series: [FlowPoint]
    let disclaimer: String
}

struct ValuationResponse: Codable {
    let ticker: String
    let name: String
    let asOfDate: String
    let per: Double
    let pbr: Double
    let perMin1y: Double?
    let perMedian1y: Double?
    let perMax1y: Double?
    let pbrMin1y: Double?
    let pbrMedian1y: Double?
    let pbrMax1y: Double?
    let disclaimer: String
}

struct ConsensusResponse: Codable {
    let ticker: String
    let name: String
    let opinionScore: Double
    let opinionText: String?
    let targetPrice: Int
    let source: String
    let disclaimer: String
}

struct TechnicalResponse: Codable {
    let ticker: String
    let name: String
    let asOfDate: String
    let close: Int
    let ma20: Double?
    let ma60: Double?
    let disparity20: Double?
    let disparity60: Double?
    let volume: Int
    let avgVolume20: Int?
    let volumeRatio: Double?
    // 표준 기술지표 — 현재 상태 계산값이지 미래 예측이 아니다
    let rsi14: Double?
    let macd: Double?
    let macdSignal: Double?
    let macdHistogram: Double?
    let bbUpper: Double?
    let bbMiddle: Double?
    let bbLower: Double?
    let bbPercentB: Double?
    let disclaimer: String
}

struct VolatilityResponse: Codable {
    let ticker: String
    let name: String
    let asOfDate: String
    let benchmark: String
    let windowDays: Int
    let beta: Double?
    let annualizedVolatilityPct: Double
    let disclaimer: String
}

struct PeerValuation: Codable, Identifiable {
    var id: String { ticker }
    let ticker: String
    let name: String
    let per: Double
    let pbr: Double
}

struct PeerComparisonResponse: Codable {
    let ticker: String
    let name: String
    let industry: String
    let peers: [PeerValuation]
    let disclaimer: String
}

/// 과거 유사 하락→회복 통계 — 미래 예측이 아니라 과거 사실 조회.
/// summary는 백엔드가 과거형/참고형 문장으로 만들어서 내려준다(app/models/schemas.py
/// 참고) — 프론트는 이 문장을 그대로 표시만 하고 직접 조립하지 않는다.
struct RecoveryHistoryResponse: Codable {
    let ticker: String
    let name: String
    let currentPrice: Int
    let currentReturnPct: Double
    let applicable: Bool
    let sufficientSample: Bool
    let sampleCount: Int
    let unresolvedCount: Int
    let avgRecoveryDays: Int?
    let medianRecoveryDays: Int?
    let summary: String
    let disclaimer: String
}

struct EarningsCalendarResponse: Codable {
    let ticker: String
    let name: String
    let reportType: String
    let deadlineDate: String
    let dDay: Int
    let note: String
    let disclaimer: String
}

struct RiskFlag: Codable, Identifiable {
    var id: String { url }
    let title: String
    let date: String
    let matchedKeyword: String
    let url: String
}

struct RiskFlagsResponse: Codable {
    let ticker: String
    let name: String
    let flags: [RiskFlag]
    let disclaimer: String
}

struct NewsArticle: Codable, Identifiable {
    var id: String { link }
    let title: String
    let description: String
    let publishedAt: String
    let link: String
}

struct NewsResponse: Codable {
    let ticker: String
    let name: String
    let articles: [NewsArticle]
    let disclaimer: String
}

struct DebateRound: Codable, Identifiable {
    var id: Int { round }
    let round: Int
    let bull: String
    let bear: String
}

struct TraderDecision: Codable {
    let decision: String
    let confidence: String
    let rationale: String
    let keyRisks: [String]
    let winningSide: String
    /// 리스크 승인 게이트가 BUY/SELL을 HOLD로 강등했을 때, 원래 판단이 여기 남는다
    let originalDecision: String?
    let gateApplied: Bool?
}

struct AgentTiming: Codable, Identifiable {
    var id: String { stage }
    let stage: String
    let seconds: Double
}

struct RiskReview: Codable {
    let verdict: String
    let concern: String
    let adjustedConfidence: String
}

struct DebateAnalysisResponse: Codable {
    let ticker: String
    let name: String
    let analystReports: [String: String]
    let debateRounds: [DebateRound]
    let decision: TraderDecision
    let riskReview: RiskReview
    let timings: [AgentTiming]?
    let totalSeconds: Double?
    let llmCalls: Int?
    let createdAt: String?
    let disclaimer: String
}

/// 지난 판단 + 그 이후 실제 주가 변화 (사후 기록 조회, 예측 아님)
struct DecisionRecord: Codable, Identifiable {
    var id: String { "\(ticker)-\(decidedAt)" }
    let ticker: String
    let name: String
    let decidedAt: String
    let decision: String
    let originalDecision: String?
    let gateApplied: Bool?
    let confidence: String?
    let rationale: String
    let riskVerdict: String?
    let priceAtDecision: Int?
    let priceNow: Int?
    let returnPct: Double?
    let daysElapsed: Int?
    /// ready=대조 완료 / pending=판단 당일이라 아직 종가 미확정 / error=조회 실패
    let status: String
}

struct DecisionHistoryResponse: Codable {
    let records: [DecisionRecord]
    let disclaimer: String
}
