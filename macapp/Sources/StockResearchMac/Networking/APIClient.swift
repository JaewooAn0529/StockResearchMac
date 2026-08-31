import Foundation

enum APIError: LocalizedError {
    case notFound(String)
    case server(Int, String)
    case decoding(Error)

    var errorDescription: String? {
        switch self {
        case .notFound(let detail): return detail
        case .server(let code, let detail): return "서버 오류(\(code)): \(detail)"
        case .decoding(let err): return "응답 파싱 실패: \(err.localizedDescription)"
        }
    }
}

/// Client for the FastAPI backend (localhost:8000). This is a personal local tool, so it connects directly without authentication.
struct APIClient {
    static let shared = APIClient()

    private let baseURL = URL(string: "http://localhost:8000")!

    private var decoder: JSONDecoder {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }

    private func request<T: Decodable>(_ path: String, method: String = "GET", queryItems: [URLQueryItem] = []) async throws -> T {
        var comps = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !queryItems.isEmpty { comps.queryItems = queryItems }

        var req = URLRequest(url: comps.url!)
        req.httpMethod = method
        // The debate endpoint makes 10 local LLM calls and can take several minutes, so allow plenty of time
        req.timeoutInterval = 300

        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.server(0, "알 수 없는 응답")
        }

        if http.statusCode == 404 {
            let detail = (try? decoder.decode([String: String].self, from: data))?["detail"] ?? "데이터 없음"
            throw APIError.notFound(detail)
        }
        guard (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.server(http.statusCode, body)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }

    func search(query: String) async throws -> [SearchResult] {
        try await request("stocks/search", queryItems: [URLQueryItem(name: "q", value: query)])
    }

    func price(_ ticker: String) async throws -> PriceResponse { try await request("stocks/\(ticker)/price") }
    func flows(_ ticker: String) async throws -> FlowsResponse { try await request("stocks/\(ticker)/flows") }
    func valuation(_ ticker: String) async throws -> ValuationResponse { try await request("stocks/\(ticker)/valuation") }
    func consensus(_ ticker: String) async throws -> ConsensusResponse { try await request("stocks/\(ticker)/consensus") }
    func technical(_ ticker: String) async throws -> TechnicalResponse { try await request("stocks/\(ticker)/technical") }
    func volatility(_ ticker: String) async throws -> VolatilityResponse { try await request("stocks/\(ticker)/volatility") }
    func peers(_ ticker: String) async throws -> PeerComparisonResponse { try await request("stocks/\(ticker)/peers") }
    func earningsCalendar(_ ticker: String) async throws -> EarningsCalendarResponse { try await request("stocks/\(ticker)/earnings-calendar") }
    func riskFlags(_ ticker: String) async throws -> RiskFlagsResponse { try await request("stocks/\(ticker)/risk-flags") }
    func news(_ ticker: String) async throws -> NewsResponse { try await request("stocks/\(ticker)/news") }

    func recoveryHistory(_ ticker: String, buyPrice: Double) async throws -> RecoveryHistoryResponse {
        try await request(
            "stocks/\(ticker)/recovery-history",
            queryItems: [URLQueryItem(name: "buy_price", value: String(buyPrice))]
        )
    }

    func debate(_ ticker: String) async throws -> DebateAnalysisResponse {
        try await request("analysis/\(ticker)/debate", method: "POST")
    }

    func decisionHistory() async throws -> DecisionHistoryResponse {
        try await request("analysis/history")
    }
}
