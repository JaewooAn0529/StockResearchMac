import SwiftUI

private let analystLabels: [String: String] = [
    "fundamentals": "Fundamentals analyst",
    "news": "News analyst",
    "technical": "Technical analyst",
    "flow": "Fund-flow analyst",
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
                    Text("Debate failed").font(.headline)
                    Text(message).font(.caption).foregroundStyle(.secondary)
                }
                .padding()
            case .loaded(let data):
                resultView(data)
            }
        }
        .navigationTitle("Multi-agent debate")
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
            Text("4 analysts → bull/bear debate → trader decision → risk review")
                .font(.subheadline)
            Text("10 local LLM calls, usually about 2 minutes · \(elapsed)s elapsed")
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

            SectionHeader(title: "Analyst reports", icon: "person.text.rectangle.fill")
            ForEach(Array(data.analystReports.keys.sorted()), id: \.self) { key in
                CardContainer(title: analystLabels[key] ?? key, icon: analystIcons[key]) {
                    Text(data.analystReports[key] ?? "").font(.callout)
                }
            }

            SectionHeader(title: "Researcher debate", icon: "bubble.left.and.bubble.right.fill")
            ForEach(data.debateRounds) { round in
                VStack(alignment: .leading, spacing: 8) {
                    Text("Round \(round.round)")
                        .font(.caption.bold())
                        .padding(.horizontal, 8).padding(.vertical, 3)
                        .background(Theme.accent.opacity(0.15), in: Capsule())
                        .foregroundStyle(Theme.accent)
                    CardContainer(title: "Bull side", icon: "arrow.up.circle", iconColor: .red) {
                        Text(round.bull).font(.callout)
                    }
                    CardContainer(title: "Bear side", icon: "arrow.down.circle", iconColor: .blue) {
                        Text(round.bear).font(.callout)
                    }
                }
            }

            if let timings = data.timings, !timings.isEmpty {
                auditCard(timings, total: data.totalSeconds, calls: data.llmCalls)
            }

            Text("This information is reference material to support investment decisions; the decision and its responsibility are your own.")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding()
    }

    /// How long each stage took — for spotting slow steps and getting a feel
    /// for what the cost would be if switched to a cloud API.
    private func auditCard(_ timings: [AgentTiming], total: Double?, calls: Int?) -> some View {
        CardContainer(title: "Run log", icon: "clock.badge.checkmark") {
            VStack(alignment: .leading, spacing: 4) {
                ForEach(timings) { t in
                    HStack {
                        Text(t.stage).font(.caption)
                        Spacer()
                        Text("\(t.seconds, specifier: "%.1f")s")
                            .font(.caption.monospacedDigit())
                            .foregroundStyle(.secondary)
                    }
                }
                Divider()
                HStack {
                    Text("Total").font(.caption.bold())
                    Spacer()
                    Text("\(total ?? 0, specifier: "%.1f")s · \(calls ?? 0) LLM calls")
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
                    Text("Confidence \(decision.confidence)").font(.caption).foregroundStyle(.secondary)
                    Text("Debate winner: \(decision.winningSide)").font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
            }

            // If the risk approval gate overturned the decision, call that out prominently
            if decision.gateApplied == true, let original = decision.originalDecision {
                Label(
                    "Rejected in risk review — downgraded \(original) → HOLD",
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
                    Text("Key risks").font(.caption.bold())
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
        return CardContainer(title: "Risk manager: \(review.verdict)", icon: icon, iconColor: color) {
            VStack(alignment: .leading, spacing: 4) {
                if !review.concern.isEmpty {
                    Text(review.concern).font(.callout)
                }
                Text("Adjusted confidence: \(review.adjustedConfidence)")
                    .font(.caption).foregroundStyle(.secondary)
                if let pct = review.suggestedPositionPct {
                    Text("Suggested max position: \(pct, specifier: "%.1f")% of the portfolio (computed from VaR)")
                        .font(.caption.bold())
                        .foregroundStyle(Theme.accent)
                }
            }
        }
    }
}
