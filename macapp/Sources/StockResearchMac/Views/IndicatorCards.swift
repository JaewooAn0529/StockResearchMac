import SwiftUI

/// 지표 10개(뉴스 포함)를 각자 독립적으로 로딩하기 위한 상태.
/// 하나가 실패해도 나머지 카드는 정상 표시된다 — 백엔드 orchestrator.gather_data와
/// 같은 철학.
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

private func formatEok(_ won: Int) -> String {
    let eok = Double(won) / 1e8
    return String(format: "%+.0f억", eok)
}

struct CardContainer<Content: View>: View {
    let title: String
    var icon: String? = nil
    var iconColor: Color? = nil  // nil이면 tinted 여부로 기본색 결정
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

// MARK: - 수급 (외국인/기관)

struct FlowCard: View {
    let state: LoadState<FlowsResponse>

    var body: some View {
        CardContainer(title: "외국인/기관 수급", icon: "arrow.left.arrow.right.circle") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(data.series.suffix(5)) { p in
                            HStack {
                                Text(p.date).foregroundStyle(.secondary)
                                Spacer()
                                Text("외 \(formatEok(p.foreignNetBuy))")
                                Text("기 \(formatEok(p.institutionNetBuy))")
                            }
                            .font(.caption)
                        }
                    }
                )
            }
        }
    }
}

// MARK: - 밸류에이션

struct ValuationCard: View {
    let state: LoadState<ValuationResponse>

    var body: some View {
        CardContainer(title: "밸류에이션 (PER/PBR)", icon: "chart.bar.fill") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        Text("PER \(data.per, specifier: "%.1f") · PBR \(data.pbr, specifier: "%.2f")")
                            .font(.subheadline.bold())
                        if let min = data.perMin1y, let max = data.perMax1y {
                            Text("1년 PER 밴드 \(min, specifier: "%.1f")~\(max, specifier: "%.1f")")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        if let min = data.pbrMin1y, let max = data.pbrMax1y {
                            Text("1년 PBR 밴드 \(min, specifier: "%.2f")~\(max, specifier: "%.2f")")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                )
            }
        }
    }
}

// MARK: - 컨센서스 (자체 분석 아님 — 시각적으로 구분)

struct ConsensusCard: View {
    let state: LoadState<ConsensusResponse>

    var body: some View {
        CardContainer(title: "증권사 컨센서스", icon: "building.columns.fill", tinted: true) {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(data.opinionText ?? "-") (\(data.opinionScore, specifier: "%.2f")) · 목표주가 \(data.targetPrice.formatted())원")
                            .font(.subheadline.bold())
                        Text("출처: \(data.source)")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                )
            }
        }
    }
}

// MARK: - 기술적 지표

struct TechnicalCard: View {
    let state: LoadState<TechnicalResponse>

    var body: some View {
        CardContainer(title: "기술적 지표", icon: "waveform.path.ecg") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        if let d20 = data.disparity20 {
                            Text("20일 이격도 \(d20, specifier: "%.1f")%").font(.caption)
                        }
                        if let d60 = data.disparity60 {
                            Text("60일 이격도 \(d60, specifier: "%.1f")%").font(.caption)
                        }
                        if let ratio = data.volumeRatio {
                            Text("거래량 20일평균 대비 \(ratio, specifier: "%.2f")배").font(.caption)
                        }
                        if data.rsi14 != nil || data.macd != nil {
                            Divider().padding(.vertical, 2)
                        }
                        if let rsi = data.rsi14 {
                            HStack(spacing: 4) {
                                Text("RSI(14) \(rsi, specifier: "%.1f")").font(.caption)
                                // 통상적 해석 구간을 색으로만 힌트 — 매매 신호가 아니다
                                Text(rsi >= 70 ? "과매수 구간" : (rsi <= 30 ? "과매도 구간" : "중립 구간"))
                                    .font(.caption2)
                                    .foregroundStyle(rsi >= 70 ? .red : (rsi <= 30 ? .blue : .secondary))
                            }
                        }
                        if let hist = data.macdHistogram {
                            Text("MACD 히스토그램 \(hist, specifier: "%+.1f")").font(.caption)
                        }
                        if let pctB = data.bbPercentB {
                            Text("볼린저 %B \(pctB, specifier: "%.2f") (0=하단 · 1=상단)").font(.caption)
                        }
                    }
                )
            }
        }
    }
}

// MARK: - 변동성/베타

struct VolatilityCard: View {
    let state: LoadState<VolatilityResponse>

    var body: some View {
        CardContainer(title: "변동성/베타", icon: "gauge.with.needle") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 4) {
                        if let beta = data.beta {
                            Text("베타 \(beta, specifier: "%.2f") (\(data.benchmark) 대비)").font(.caption)
                        }
                        Text("연율화 변동성 \(data.annualizedVolatilityPct, specifier: "%.1f")%").font(.caption)
                    }
                )
            }
        }
    }
}

// MARK: - 동종업계 비교

struct PeersCard: View {
    let state: LoadState<PeerComparisonResponse>

    var body: some View {
        CardContainer(title: "동종업계 비교", icon: "square.grid.2x2") {
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

// MARK: - 실적발표 캘린더

struct EarningsCalendarCard: View {
    let state: LoadState<EarningsCalendarResponse>

    var body: some View {
        CardContainer(title: "다음 정기공시 D-day", icon: "calendar") {
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

// MARK: - 리스크 체크리스트

struct RiskFlagsCard: View {
    let state: LoadState<RiskFlagsResponse>

    var body: some View {
        CardContainer(title: "리스크 체크리스트", icon: "exclamationmark.triangle.fill") {
            CardStateView(state: state) { data in
                AnyView(
                    Group {
                        if data.flags.isEmpty {
                            Label("최근 180일 내 특이 공시 없음", systemImage: "checkmark.circle")
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
