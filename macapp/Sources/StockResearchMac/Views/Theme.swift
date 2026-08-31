import SwiftUI

/// Colors/card styles reused throughout the app. Only the change-percent
/// red/blue (a Korean stock market convention) is fixed; every other accent
/// color is unified to a single indigo so the indicator cards don't feel
/// cluttered with too many colors.
enum Theme {
    static let accent = Color.indigo
    static func changeColor(_ pct: Double) -> Color { pct >= 0 ? .red : .blue }
}

/// A card with a shadow + border. It used to just apply background-color opacity, which made the screen feel flat.
struct CardBackground: ViewModifier {
    var tinted: Bool = false

    func body(content: Content) -> some View {
        content
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(tinted ? Theme.accent.opacity(0.08) : Color(nsColor: .controlBackgroundColor))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .strokeBorder(tinted ? Theme.accent.opacity(0.25) : Color.primary.opacity(0.08), lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.06), radius: 6, x: 0, y: 2)
    }
}

extension View {
    func cardStyle(tinted: Bool = false) -> some View {
        modifier(CardBackground(tinted: tinted))
    }
}

/// Shows the change percent as a colored pill badge — reads at a glance better than just changing text color.
struct ChangeBadge: View {
    let pct: Double

    var body: some View {
        Text(String(format: "%+.2f%%", pct))
            .font(.caption.bold())
            .contentTransition(.numericText(value: pct))
            .foregroundStyle(Theme.changeColor(pct))
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(Theme.changeColor(pct).opacity(0.15), in: Capsule())
            .animation(.spring(response: 0.4, dampingFraction: 0.8), value: pct)
    }
}

/// A section title placed above a card grid. Adds an icon so the indicator cards read as visually distinct groups.
struct SectionHeader: View {
    let title: String
    var icon: String? = nil

    var body: some View {
        HStack(spacing: 6) {
            if let icon {
                Image(systemName: icon).foregroundStyle(Theme.accent)
            }
            Text(title).font(.title3.bold())
        }
    }
}

// MARK: - Pixel-art characters (shared by DebateOfficeView, OfficeAmbientView)

/// Reads pixel-art PNGs made with a local SD model from Resources/ in Bundle.module.
/// See assets-gen/generate_batch.py.
func pixelImage(_ name: String) -> Image {
    if let url = Bundle.module.url(forResource: name, withExtension: "png", subdirectory: "Resources"),
       let nsImage = NSImage(contentsOf: url) {
        return Image(nsImage: nsImage)
    }
    // Silently swallowing an asset-name typo leaves a lone person icon on
    // screen with no clue why (this actually happened with a furn_SOFA →
    // furn_SOFA_FRONT typo). Log it to the console during development so it's noticed right away.
    print("[asset] not found: \(name).png")
    return Image(systemName: "exclamationmark.triangle.fill")
}

let pixelCharacterRoster: [String: (name: String, image: String, accent: Color)] = [
    "fundamentals": ("펀더멘털 분석가", "sprite_fundamentals_idle", .indigo),
    "news": ("뉴스 분석가", "sprite_news_idle", .indigo),
    "technical": ("기술적 분석가", "sprite_technical_idle", .indigo),
    "flow": ("수급 분석가", "sprite_flow_idle", .indigo),
    "bull": ("매수 연구원", "sprite_bull_idle", .red),
    "bear": ("매도 연구원", "sprite_bear_idle", .blue),
    "trader": ("트레이더", "sprite_trader_idle", Theme.accent),
    "risk": ("리스크 매니저", "sprite_risk_idle", .orange),
]
