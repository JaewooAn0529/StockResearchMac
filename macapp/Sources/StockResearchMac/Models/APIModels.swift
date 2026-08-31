import Foundation

// Mirrors app/models/schemas.py on the backend 1:1. Field names are kept in
// snake_case here and converted in bulk by APIClient's JSONDecoder via .convertFromSnakeCase.

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
    // Standard technical indicators — these are computed current-state values, not future predictions
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

/// Statistics on similar past drop-and-recovery episodes — this looks up historical
/// facts, not future predictions. The backend generates `summary` as a past-tense,
/// reference-style sentence (see app/models/schemas.py) — the frontend just displays
/// it as-is rather than assembling it itself.
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
    /// When the risk approval gate downgrades a BUY/SELL to HOLD, the original decision is preserved here
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

/// A past decision plus the actual price change since then (a historical record lookup, not a prediction)
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
    /// ready = comparison complete / pending = decision was made today so today's close isn't final yet / error = lookup failed
    let status: String
}

struct DecisionHistoryResponse: Codable {
    let records: [DecisionRecord]
    let disclaimer: String
}
