import Foundation

/// 즐겨찾기 종목을 UserDefaults에 저장한다. 개인용 로컬 도구라 서버 동기화나
/// SwiftData 같은 무거운 저장소는 과하다.
///
/// 티커만 저장하면 홈 화면 카드를 그릴 때마다 이름/시장구분을 다시 조회해야
/// 해서, 즐겨찾기에 넣는 시점(검색 결과나 종목상세 화면)에 이미 들고 있는
/// SearchResult를 그대로 저장해둔다.
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
