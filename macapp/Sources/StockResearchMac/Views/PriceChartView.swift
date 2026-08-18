import Charts
import SwiftUI

/// 종가 라인 + 거래량 바. 캔들스틱은 Swift Charts에 기본 제공이 안 돼(RectangleMark로
/// 직접 만들어야 함) 이번 패스는 라인으로 간다.
struct PriceChartView: View {
    let ohlcv: [OHLCVPoint]

    private struct Point {
        let date: Date
        let close: Int
        let volume: Int
    }

    private var points: [Point] {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return ohlcv.compactMap { p in
            guard let d = formatter.date(from: p.date) else { return nil }
            return Point(date: d, close: p.close, volume: p.volume)
        }
    }

    /// 조회 기간 시작 대비 상승/하락으로 차트 색을 정한다 — 카드/배지의 등락률
    /// 색과 같은 규칙(빨강=상승/파랑=하락)을 차트에도 그대로 적용.
    private var trendColor: Color {
        guard let first = points.first, let last = points.last else { return Theme.accent }
        return Theme.changeColor(Double(last.close - first.close))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Chart(points, id: \.date) { p in
                AreaMark(x: .value("날짜", p.date), y: .value("종가", p.close))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [trendColor.opacity(0.25), trendColor.opacity(0.02)],
                            startPoint: .top, endPoint: .bottom
                        )
                    )
                    .interpolationMethod(.catmullRom)
                LineMark(x: .value("날짜", p.date), y: .value("종가", p.close))
                    .foregroundStyle(trendColor)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                    .interpolationMethod(.catmullRom)
            }
            .frame(height: 180)
            .chartYAxis { AxisMarks(position: .trailing) }
            .chartYScale(domain: .automatic(includesZero: false))

            Chart(points, id: \.date) { p in
                BarMark(x: .value("날짜", p.date), y: .value("거래량", p.volume))
                    .foregroundStyle(.secondary.opacity(0.5))
            }
            .frame(height: 50)
            .chartYAxis(.hidden)
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(Color(nsColor: .controlBackgroundColor))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(Color.primary.opacity(0.08), lineWidth: 1)
        )
    }
}
