import SwiftUI

/// Past debate decisions and the actual price moves that followed.
///
/// ⚠️ This is not a performance guarantee claiming "this agent gets it right,"
/// nor a future prediction — it's a historical record lookup: "here's what was
/// decided at that time, and here's how the price moved afterward." All screen
/// copy is written strictly in the past tense accordingly.
struct DecisionHistoryView: View {
    @State private var state: LoadState<DecisionHistoryResponse> = .loading

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeader(title: "지난 판단 되돌아보기", icon: "clock.arrow.circlepath")

                CardStateView(state: state) { data in
                    AnyView(
                        Group {
                            if data.records.isEmpty {
                                Text("아직 기록된 판단이 없습니다. 종목 화면에서 토론을 실행하면 여기에 쌓입니다.")
                                    .font(.callout)
                                    .foregroundStyle(.secondary)
                            } else {
                                VStack(spacing: 10) {
                                    ForEach(data.records) { record in
                                        recordCard(record)
                                    }
                                }
                            }
                        }
                    )
                }

                if case .loaded(let data) = state {
                    Text(data.disclaimer)
                        .font(.caption2.bold())
                        .foregroundStyle(.orange)
                }
            }
            .padding()
        }
        .navigationTitle("판단 기록")
        .task { await load() }
    }

    private func load() async {
        do {
            state = .loaded(try await APIClient.shared.decisionHistory())
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    private func recordCard(_ r: DecisionRecord) -> some View {
        let color: Color = r.decision == "BUY" ? .red : (r.decision == "SELL" ? .blue : .secondary)

        return VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(r.name).font(.subheadline.bold())
                Text(r.decision)
                    .font(.caption.bold())
                    .foregroundStyle(color)
                    .padding(.horizontal, 8).padding(.vertical, 2)
                    .background(color.opacity(0.15), in: Capsule())
                if r.gateApplied == true, let original = r.originalDecision {
                    Label("\(original)→HOLD", systemImage: "shield.lefthalf.filled")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                }
                Spacer()
                Text(String(r.decidedAt.prefix(10)))
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            // How the price moved after the decision (just a factual lookup, not a performance evaluation)
            switch r.status {
            case "ready":
                if let then = r.priceAtDecision, let now = r.priceNow, let pct = r.returnPct {
                    HStack(spacing: 6) {
                        Text("판단 시점 \(then.formatted())원 → 최근 \(now.formatted())원")
                            .font(.caption)
                        Text(String(format: "%+.2f%%", pct))
                            .font(.caption.bold())
                            .foregroundStyle(Theme.changeColor(pct))
                        if let days = r.daysElapsed {
                            Text("· \(days)일 경과").font(.caption2).foregroundStyle(.secondary)
                        }
                    }
                }
            case "pending":
                Text("판단 당일이라 아직 대조할 종가가 없습니다")
                    .font(.caption2).foregroundStyle(.secondary)
            default:
                Text("주가 조회에 실패했습니다")
                    .font(.caption2).foregroundStyle(.secondary)
            }

            Text(r.rationale)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(3)
        }
        .cardStyle()
    }
}
