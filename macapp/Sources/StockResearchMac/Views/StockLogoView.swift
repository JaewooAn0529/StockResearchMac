import SwiftUI

/// A listed company's logo, fetched from Naver Finance's public per-ticker
/// logo endpoint (a different host from KRX/KIND, so it isn't affected by
/// the KRX-side rate limiting/blocking this app has run into elsewhere).
/// Falls back to a generic building icon while loading or when a given
/// ticker has no logo on file (e.g. very recent listings).
struct StockLogoView: View {
    let ticker: String
    var size: CGFloat = 32

    private var url: URL? {
        URL(string: "https://ssl.pstatic.net/imgstock/fn/real/logo/png/stock/Stock\(ticker).png")
    }

    var body: some View {
        AsyncImage(url: url) { phase in
            if let image = phase.image {
                image
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .padding(size * 0.08)
            } else {
                Image(systemName: "building.2.fill")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .foregroundStyle(.secondary)
                    .padding(size * 0.22)
            }
        }
        .frame(width: size, height: size)
        // Most listed-company logos are drawn for a light background, so a
        // white plate keeps them legible over this app's dark office scene.
        .background(Color.white, in: RoundedRectangle(cornerRadius: size * 0.28, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: size * 0.28, style: .continuous)
                .strokeBorder(Color.black.opacity(0.08))
        )
        .clipShape(RoundedRectangle(cornerRadius: size * 0.28, style: .continuous))
    }
}
