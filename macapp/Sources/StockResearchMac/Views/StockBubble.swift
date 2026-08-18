import SwiftUI

/// 즐겨찾기 종목을 카드로 따로 안 띄우고, 오피스에 있는 캐릭터 머리 위에
/// 말풍선처럼 붙여서 보여준다 — 배경 장면과 붕 떠 보이지 않게.
struct StockBubble: View {
    let result: SearchResult

    @State private var price: PriceResponse?

    var body: some View {
        NavigationLink(value: StockRoute(ticker: result.ticker)) {
            VStack(spacing: 0) {
                VStack(spacing: 2) {
                    Text(result.name)
                        .font(.caption.bold())
                        .lineLimit(1)
                    if let price {
                        HStack(spacing: 4) {
                            Text("\(price.currentPrice.formatted())원")
                                .font(.caption2)
                                .monospacedDigit()
                                .contentTransition(.numericText())
                            Text(String(format: "%+.1f%%", price.changePct))
                                .font(.caption2.bold())
                                .foregroundStyle(Theme.changeColor(price.changePct))
                        }
                    } else {
                        ProgressView().controlSize(.mini)
                    }
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 10, style: .continuous).strokeBorder(.white.opacity(0.5), lineWidth: 1))
                .shadow(color: .black.opacity(0.35), radius: 4, y: 2)

                // 말풍선 꼬리 — 캐릭터를 가리키게 아래로
                Triangle()
                    .fill(.thinMaterial)
                    .frame(width: 10, height: 6)
            }
        }
        .buttonStyle(.plain)
        .task(id: result.ticker) {
            price = try? await APIClient.shared.price(result.ticker)
        }
    }
}

private struct Triangle: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.midX, y: rect.maxY))
        path.addLine(to: CGPoint(x: rect.minX, y: rect.minY))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.minY))
        path.closeSubpath()
        return path
    }
}
