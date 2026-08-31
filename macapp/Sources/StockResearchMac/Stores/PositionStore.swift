import Foundation

/// The buy price/date the user entered. Since this is purely user input, no
/// server-side calculation is needed (return is just current price minus buy
/// price, a simple factual calculation), so it's stored client-side only.
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
