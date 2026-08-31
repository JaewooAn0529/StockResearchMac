import Charts
import SwiftUI

/// Closing-price line + volume bars. Swift Charts doesn't provide candlesticks
/// out of the box (you'd have to build them yourself with RectangleMark), so
/// this pass goes with a line chart instead.
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

    /// Decides the chart color based on whether it's up or down versus the
    /// start of the queried period — applies the same rule to the chart as
    /// the change-percent color used on cards/badges (red = up, blue = down).
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
