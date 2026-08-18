import SwiftUI

/// 앱 전체에서 재사용하는 색/카드 스타일. 등락률 빨강/파랑(국내 증시 관례)만
/// 고정이고, 나머지 강조색은 인디고 하나로 통일해서 지표 카드가 여러 색으로
/// 산만해지지 않게 한다.
enum Theme {
    static let accent = Color.indigo
    static func changeColor(_ pct: Double) -> Color { pct >= 0 ? .red : .blue }
}

/// 그림자+테두리가 있는 카드. 기존엔 배경색 opacity만 줘서 화면이 밋밋했다.
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

/// 등락률을 색이 있는 알약 배지로 — 텍스트 색만 바꾸는 것보다 한눈에 들어온다.
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

/// 카드 그리드 위에 붙는 섹션 타이틀. 아이콘을 달아서 지표 카드들이 서로
/// 구분돼 보이게 한다.
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

// MARK: - 픽셀아트 캐릭터 (DebateOfficeView, OfficeAmbientView가 공유)

/// Bundle.module의 Resources/에서 로컬 SD로 만든 픽셀아트 PNG를 읽어온다.
/// assets-gen/generate_batch.py 참고.
func pixelImage(_ name: String) -> Image {
    if let url = Bundle.module.url(forResource: name, withExtension: "png", subdirectory: "Resources"),
       let nsImage = NSImage(contentsOf: url) {
        return Image(nsImage: nsImage)
    }
    // 에셋 이름 오타를 조용히 넘기면 화면에 사람 아이콘이 덩그러니 남아 원인을
    // 찾기 어렵다(실제로 furn_SOFA → furn_SOFA_FRONT 오타로 겪음).
    // 개발 중에는 콘솔에 남겨서 바로 알아채게 한다.
    print("[asset] 못 찾음: \(name).png")
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
