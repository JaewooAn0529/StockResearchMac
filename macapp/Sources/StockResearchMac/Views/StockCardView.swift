import SwiftUI

/// 홈 화면(즐겨찾기)과 검색 결과 양쪽에서 쓰는 카드. 현재가/등락률은 자체적으로
/// price 엔드포인트를 호출해서 채운다 — 목록 화면이 상세 데이터까지 몰아서
/// 들고 있을 필요가 없게 카드가 자기 몫만 책임진다.
struct StockCardView: View {
    let result: SearchResult
    @EnvironmentObject private var favorites: FavoritesStore

    @State private var price: PriceResponse?
    @State private var loadFailed = false
    @State private var favoriteBounce = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(result.name)
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text("\(result.ticker) · \(result.market)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button {
                    favorites.toggle(result)
                    favoriteBounce.toggle()
                } label: {
                    Image(systemName: favorites.contains(result.ticker) ? "star.fill" : "star")
                        .foregroundStyle(favorites.contains(result.ticker) ? .yellow : .secondary)
                        .symbolEffect(.bounce, value: favoriteBounce)
                }
                .buttonStyle(.plain)
            }

            Group {
                if let price {
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Text("\(price.currentPrice.formatted())원")
                            .font(.title2.bold())
                            .monospacedDigit()
                            .contentTransition(.numericText())
                        ChangeBadge(pct: price.changePct)
                    }
                    .transition(.opacity.combined(with: .scale(scale: 0.97, anchor: .leading)))
                } else if loadFailed {
                    Text("시세 조회 실패").font(.caption).foregroundStyle(.secondary)
                } else {
                    ProgressView().controlSize(.small)
                }
            }
            .animation(.spring(response: 0.4, dampingFraction: 0.82), value: price?.currentPrice)
        }
        .cardStyle()
        .task(id: result.ticker) {
            do {
                price = try await APIClient.shared.price(result.ticker)
            } catch {
                loadFailed = true
            }
        }
    }
}
