import SwiftUI

/// State for loading each of the 10 indicators (including news) independently.
/// If one fails, the other cards still display normally — the same philosophy
/// as the backend's orchestrator.gather_data.
enum LoadState<T> {
    case loading
    case loaded(T)
    case failed(String)

    init(result: Result<T, Error>) {
        switch result {
        case .success(let value): self = .loaded(value)
        case .failure(let error): self = .failed(error.localizedDescription)
        }
    }
}

private func formatBillions(_ won: Int) -> String {
    let billions = Double(won) / 1e9
    return String(format: "%+.1fB", billions)
}

struct CardContainer<Content: View>: View {
    let title: String
    var icon: String? = nil
    var iconColor: Color? = nil  // if nil, the default color is decided by `tinted`
    var tinted: Bool = false
    @ViewBuilder var content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                if let icon {
                    Image(systemName: icon)
                        .foregroundStyle(iconColor ?? (tinted ? Theme.accent : .secondary))
                }
                Text(title).font(.subheadline.bold())
            }
            content()
        }
        .cardStyle(tinted: tinted)
    }
}

struct CardStateView<T>: View {
    let state: LoadState<T>
    @ViewBuilder let content: (T) -> AnyView

    var body: some View {
        Group {
            switch state {
            case .loading:
                ProgressView().controlSize(.small)
                    .transition(.opacity)
            case .failed(let message):
                Text(message).font(.caption).foregroundStyle(.secondary)
                    .transition(.opacity)
            case .loaded(let value):
                content(value)
                    .transition(.opacity.combined(with: .scale(scale: 0.97, anchor: .top)))
            }
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.82), value: isLoaded)
    }

    private var isLoaded: Bool {
        if case .loaded = state { return true }
        return false
    }
}

// MARK: - Flow (foreign/institutional)

struct FlowCard: View {
    let state: LoadState<FlowsResponse>

    var body: some View {
        CardContainer(title: "Foreign/institutional flows", icon: "arrow.left.arrow.right.circle") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(data.series.suffix(5)) { p in
                            HStack {
                                Text(p.date).foregroundStyle(.secondary)
                                Spacer()
                                Text("Frgn ₩\(formatBillions(p.foreignNetBuy))")
                                Text("Inst ₩\(formatBillions(p.institutionNetBuy))")
                            }
                            .font(.caption)
                        }
                    }
                )
            }
        }
    }
}

// MARK: - Valuation

struct ValuationCard: View {
    let state: LoadState<ValuationResponse>

    var body: some View {
        CardContainer(title: "Valuation (PER/PBR)", icon: "chart.bar.fill") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        Text("PER \(data.per, specifier: "%.1f") · PBR \(data.pbr, specifier: "%.2f")")
                            .font(.subheadline.bold())
                        if let min = data.perMin1y, let max = data.perMax1y {
                            Text("1-year PER band \(min, specifier: "%.1f")~\(max, specifier: "%.1f")")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        if let min = data.pbrMin1y, let max = data.pbrMax1y {
                            Text("1-year PBR band \(min, specifier: "%.2f")~\(max, specifier: "%.2f")")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                )
            }
        }
    }
}

// MARK: - Consensus (not our own analysis — visually distinguished)

struct ConsensusCard: View {
    let state: LoadState<ConsensusResponse>

    var body: some View {
        CardContainer(title: "Brokerage consensus", icon: "building.columns.fill", tinted: true) {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(data.opinionText ?? "-") (\(data.opinionScore, specifier: "%.2f")) · Target ₩\(data.targetPrice.formatted())")
                            .font(.subheadline.bold())
                        Text("Source: \(data.source)")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                )
            }
        }
    }
}

// MARK: - Technical indicators

struct TechnicalCard: View {
    let state: LoadState<TechnicalResponse>

    var body: some View {
        CardContainer(title: "Technical indicators", icon: "waveform.path.ecg") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        if let d20 = data.disparity20 {
                            Text("20-day disparity \(d20, specifier: "%.1f")%").font(.caption)
                        }
                        if let d60 = data.disparity60 {
                            Text("60-day disparity \(d60, specifier: "%.1f")%").font(.caption)
                        }
                        if let ratio = data.volumeRatio {
                            Text("Volume \(ratio, specifier: "%.2f")x the 20-day average").font(.caption)
                        }
                        if data.rsi14 != nil || data.macd != nil {
                            Divider().padding(.vertical, 2)
                        }
                        if let rsi = data.rsi14 {
                            HStack(spacing: 4) {
                                Text("RSI(14) \(rsi, specifier: "%.1f")").font(.caption)
                                // Just a color hint for the conventional interpretation range — not a trading signal
                                Text(rsi >= 70 ? "Overbought" : (rsi <= 30 ? "Oversold" : "Neutral"))
                                    .font(.caption2)
                                    .foregroundStyle(rsi >= 70 ? .red : (rsi <= 30 ? .blue : .secondary))
                            }
                        }
                        if let hist = data.macdHistogram {
                            Text("MACD histogram \(hist, specifier: "%+.1f")").font(.caption)
                        }
                        if let pctB = data.bbPercentB {
                            Text("Bollinger %B \(pctB, specifier: "%.2f") (0 = lower · 1 = upper)").font(.caption)
                        }
                    }
                )
            }
        }
    }
}

// MARK: - Volatility/beta

struct VolatilityCard: View {
    let state: LoadState<VolatilityResponse>

    var body: some View {
        CardContainer(title: "Volatility/beta", icon: "gauge.with.needle") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        if let beta = data.beta {
                            Text("Beta \(beta, specifier: "%.2f") (vs \(data.benchmark))").font(.caption)
                        }
                        Text("Annualized volatility \(data.annualizedVolatilityPct, specifier: "%.1f")%").font(.caption)
                        Divider().padding(.vertical, 2)
                        Text("1-day 95% VaR (historical) \(data.var951dayHistoricalPct, specifier: "%.2f")%")
                            .font(.caption)
                        Text("1-day 95% VaR (normal dist.) \(data.var951dayPct, specifier: "%.2f")%")
                            .font(.caption2).foregroundStyle(.secondary)
                        Text("Suggested max position \(data.suggestedMaxPositionPct, specifier: "%.1f")% (2% daily risk budget)")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                )
            }
        }
    }
}

// MARK: - RSI signal statistics

struct RsiSignalStatsCard: View {
    let state: LoadState<RsiSignalStatsResponse>

    var body: some View {
        CardContainer(title: "RSI signal statistics", icon: "chart.bar.xaxis") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Text("Sample: \(data.sampleCount) cases")
                                .font(.caption.bold())
                            if data.statisticallySignificant {
                                Text("Statistically significant").font(.caption2)
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 6).padding(.vertical, 2)
                                    .background(.green, in: Capsule())
                            } else if !data.sufficientSample {
                                Text("Insufficient sample").font(.caption2)
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 6).padding(.vertical, 2)
                                    .background(.secondary, in: Capsule())
                            }
                        }
                        if let hitRate = data.hitRatePct {
                            Text("After RSI fell below \(data.rsiThreshold, specifier: "%.0f"): \(hitRate, specifier: "%.0f")% rose \(data.gainThresholdPct, specifier: "%.0f")%+ within \(data.windowDays) trading days")
                                .font(.caption)
                        }
                        if let p = data.pValue {
                            Text("p = \(p, specifier: "%.3f")").font(.caption2).foregroundStyle(.secondary)
                        }
                        Text(data.summary)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                )
            }
        }
    }
}

// MARK: - Peer comparison

struct PeersCard: View {
    let state: LoadState<PeerComparisonResponse>

    var body: some View {
        CardContainer(title: "Peer comparison", icon: "square.grid.2x2") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        Text(data.industry).font(.caption).foregroundStyle(.secondary)
                        ForEach(data.peers) { p in
                            HStack {
                                Text(p.name)
                                Spacer()
                                Text("PER \(p.per, specifier: "%.1f") / PBR \(p.pbr, specifier: "%.2f")")
                                    .foregroundStyle(.secondary)
                            }
                            .font(.caption)
                        }
                    }
                )
            }
        }
    }
}

// MARK: - Earnings calendar

struct EarningsCalendarCard: View {
    let state: LoadState<EarningsCalendarResponse>

    var body: some View {
        CardContainer(title: "Next periodic filing D-day", icon: "calendar") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(data.reportType) D-\(data.dDay) (\(data.deadlineDate))")
                            .font(.subheadline.bold())
                        Text(data.note).font(.caption2).foregroundStyle(.secondary)
                    }
                )
            }
        }
    }
}

// MARK: - Risk checklist

struct RiskFlagsCard: View {
    let state: LoadState<RiskFlagsResponse>

    var body: some View {
        CardContainer(title: "Risk checklist", icon: "exclamationmark.triangle.fill") {
            CardStateView(state: state) { data in
                AnyView(
                    Group {
                        if data.flags.isEmpty {
                            Label("No notable filings in the last 180 days", systemImage: "checkmark.circle")
                                .font(.caption).foregroundStyle(.secondary)
                        } else {
                            VStack(alignment: .leading, spacing: 6) {
                                ForEach(data.flags) { flag in
                                    Link(destination: URL(string: flag.url)!) {
                                        Label("\(flag.title) (\(flag.date))", systemImage: "exclamationmark.triangle.fill")
                                            .font(.caption)
                                            .foregroundStyle(.orange)
                                    }
                                }
                            }
                        }
                    }
                )
            }
        }
    }
}
