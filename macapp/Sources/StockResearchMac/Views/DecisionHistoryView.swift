import SwiftUI

/// 지난 토론 판단들과 그 이후 실제 주가 변화.
///
/// ⚠️ 이건 "이 에이전트가 잘 맞힌다"는 성능 보장이나 미래 예측이 아니라,
/// "그때 이렇게 판단했고 이후 주가는 이렇게 움직였다"는 사후 기록 조회다.
/// 화면 문구도 전부 과거형으로만 쓴다.
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

            // 판단 이후 주가가 어떻게 움직였는지 (사실 조회일 뿐, 성능 평가가 아님)
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
