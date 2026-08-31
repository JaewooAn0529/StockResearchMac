import Foundation

/// Persists favorited stocks to UserDefaults. This is a personal local tool, so
/// server sync or a heavier store like SwiftData would be overkill.
///
/// If we only stored the ticker, we'd have to re-fetch the name/market every
/// time a home screen card is rendered, so instead we save the SearchResult
/// we already have on hand at the moment it's favorited (from the search
/// results or the stock detail screen).
@MainActor
final class FavoritesStore: ObservableObject {
    @Published private(set) var items: [SearchResult]

    private let key = "favoriteStocks"

    init() {
        if let data = UserDefaults.standard.data(forKey: key),
           let decoded = try? JSONDecoder().decode([SearchResult].self, from: data) {
            items = decoded
        } else {
            items = []
        }
    }

    func contains(_ ticker: String) -> Bool {
        items.contains { $0.ticker == ticker }
    }

    func toggle(_ result: SearchResult) {
        if let idx = items.firstIndex(where: { $0.ticker == result.ticker }) {
            items.remove(at: idx)
        } else {
            items.append(result)
        }
        if let data = try? JSONEncoder().encode(items) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }
}
