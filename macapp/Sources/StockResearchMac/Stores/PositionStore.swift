import Foundation

/// 사용자가 입력한 매수가/매수일. 순수 사용자 입력값이라 서버 계산이 필요
/// 없고(수익률은 현재가 - 매수가라는 단순 사실 계산), 클라이언트에만 저장한다.
struct Position: Codable, Equatable {
    var buyPrice: Double
    var buyDate: Date
}

@MainActor
final class PositionStore: ObservableObject {
    @Published private(set) var positions: [String: Position]

    private let key = "positions"

    init() {
        if let data = UserDefaults.standard.data(forKey: key),
           let decoded = try? JSONDecoder().decode([String: Position].self, from: data) {
            positions = decoded
        } else {
            positions = [:]
        }
    }

    func position(for ticker: String) -> Position? {
        positions[ticker]
    }

    func set(_ position: Position, for ticker: String) {
        positions[ticker] = position
        persist()
    }

    func clear(for ticker: String) {
        positions.removeValue(forKey: ticker)
        persist()
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(positions) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }
}
