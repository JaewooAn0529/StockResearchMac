import SwiftUI

private let analystLabels: [String: String] = [
    "fundamentals": "펀더멘털 분석가",
    "news": "뉴스 분석가",
    "technical": "기술적 분석가",
    "flow": "수급 분석가",
]

private let analystIcons: [String: String] = [
    "fundamentals": "chart.bar.fill",
    "news": "newspaper.fill",
    "technical": "waveform.path.ecg",
    "flow": "arrow.left.arrow.right.circle",
]

struct DebateView: View {
    let ticker: String

    @State private var state: LoadState<DebateAnalysisResponse> = .loading
    @State private var elapsed = 0

    var body: some View {
        ScrollView {
            switch state {
            case .loading:
                loadingView
            case .failed(let message):
                VStack(spacing: 12) {
                    Text("토론 실패").font(.headline)
                    Text(message).font(.caption).foregroundStyle(.secondary)
                }
                .padding()
            case .loaded(let data):
                resultView(data)
            }
        }
        .navigationTitle("멀티에이전트 토론")
        .task { await runDebate() }
        .task {
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))
                elapsed += 1
            }
        }
    }

    private var loadingView: some View {
        VStack(spacing: 14) {
            Image(systemName: "bubble.left.and.bubble.right.fill")
                .font(.system(size: 40))
                .foregroundStyle(Theme.accent)
                .symbolEffect(.pulse, options: .repeating)
            Text("분석가 4인 → bull/bear 토론 → 트레이더 판단 → 리스크 검토")
                .font(.subheadline)
            Text("로컬 LLM 호출 10회, 보통 2분 내외 걸립니다 · \(elapsed)초 경과")
                .font(.caption)
                .foregroundStyle(.secondary)
                .contentTransition(.numericText())
                .animation(.spring(response: 0.3, dampingFraction: 0.8), value: elapsed)
        }
        .frame(maxWidth: .infinity, minHeight: 300)
    }

    private func runDebate() async {
        do {
            let result = try await APIClient.shared.debate(ticker)
            withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
                state = .loaded(result)
            }
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    private func resultView(_ data: DebateAnalysisResponse) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            DebateOfficeView(data: data)

            decisionCard(data.decision)
            riskReviewCard(data.riskReview)

            SectionHeader(title: "분석가 리포트", icon: "person.text.rectangle.fill")
            ForEach(Array(data.analystReports.keys.sorted()), id: \.self) { key in
                CardContainer(title: analystLabels[key] ?? key, icon: analystIcons[key]) {
                    Text(data.analystReports[key] ?? "").font(.callout)
                }
            }

            SectionHeader(title: "연구원 토론", icon: "bubble.left.and.bubble.right.fill")
            ForEach(data.debateRounds) { round in
                VStack(alignment: .leading, spacing: 8) {
                    Text("\(round.round)라운드")
                        .font(.caption.bold())
                        .padding(.horizontal, 8).padding(.vertical, 3)
                        .background(Theme.accent.opacity(0.15), in: Capsule())
                        .foregroundStyle(Theme.accent)
                    CardContainer(title: "매수 측", icon: "arrow.up.circle", iconColor: .red) {
                        Text(round.bull).font(.callout)
                    }
                    CardContainer(title: "매도 측", icon: "arrow.down.circle", iconColor: .blue) {
                        Text(round.bear).font(.callout)
                    }
                }
            }

            if let timings = data.timings, !timings.isEmpty {
                auditCard(timings, total: data.totalSeconds, calls: data.llmCalls)
            }

            Text("이 정보는 투자 판단을 돕기 위한 참고 자료이며, 투자 판단과 그 책임은 본인에게 있습니다.")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding()
    }

    /// How long each stage took — for spotting slow steps and getting a feel
    /// for what the cost would be if switched to a cloud API.
    private func auditCard(_ timings: [AgentTiming], total: Double?, calls: Int?) -> some View {
        CardContainer(title: "실행 기록", icon: "clock.badge.checkmark") {
            VStack(alignment: .leading, spacing: 4) {
                ForEach(timings) { t in
                    HStack {
                        Text(t.stage).font(.caption)
                        Spacer()
                        Text("\(t.seconds, specifier: "%.1f")초")
                            .font(.caption.monospacedDigit())
                            .foregroundStyle(.secondary)
                    }
                }
                Divider()
                HStack {
                    Text("합계").font(.caption.bold())
                    Spacer()
                    Text("\(total ?? 0, specifier: "%.1f")초 · LLM \(calls ?? 0)회")
                        .font(.caption.bold().monospacedDigit())
                }
            }
        }
    }

    private func decisionCard(_ decision: TraderDecision) -> some View {
        let color: Color = decision.decision == "BUY" ? .red : (decision.decision == "SELL" ? .blue : .secondary)
        let icon = decision.decision == "BUY" ? "arrow.up.circle.fill" : (decision.decision == "SELL" ? "arrow.down.circle.fill" : "minus.circle.fill")

        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Label(decision.decision, systemImage: icon)
                    .font(.system(size: 30, weight: .bold))
                    .foregroundStyle(color)
                VStack(alignment: .leading, spacing: 1) {
                    Text("확신도 \(decision.confidence)").font(.caption).foregroundStyle(.secondary)
                    Text("토론 우세: \(decision.winningSide)").font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
            }

            // If the risk approval gate overturned the decision, call that out prominently
            if decision.gateApplied == true, let original = decision.originalDecision {
                Label(
                    "리스크 검토에서 반려되어 \(original) → HOLD로 강등되었습니다",
                    systemImage: "shield.lefthalf.filled"
                )
                .font(.caption.bold())
                .foregroundStyle(.orange)
                .padding(.horizontal, 10).padding(.vertical, 6)
                .background(Color.orange.opacity(0.15), in: RoundedRectangle(cornerRadius: 8))
            }

            Text(decision.rationale).font(.body)
            if !decision.keyRisks.isEmpty {
                VStack(alignment: .leading, spacing: 3) {
                    Text("핵심 위험").font(.caption.bold())
                    ForEach(decision.keyRisks, id: \.self) { risk in
                        Text("· \(risk)").font(.caption)
                    }
                }
            }
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(color.opacity(0.1)))
        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(color.opacity(0.35), lineWidth: 1.5))
        .transition(.scale(scale: 0.9).combined(with: .opacity))
    }

    private func riskReviewCard(_ review: RiskReview) -> some View {
        let (icon, color): (String, Color) = {
            switch review.verdict {
            case "approve": return ("checkmark.seal.fill", .green)
            case "reject": return ("xmark.seal.fill", .red)
            default: return ("exclamationmark.triangle.fill", .orange)
            }
        }()
        return CardContainer(title: "리스크 매니저: \(review.verdict)", icon: icon, iconColor: color) {
            VStack(alignment: .leading, spacing: 4) {
                if !review.concern.isEmpty {
                    Text(review.concern).font(.callout)
                }
                Text("조정된 확신도: \(review.adjustedConfidence)")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}
