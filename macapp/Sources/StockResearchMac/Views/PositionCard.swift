import SwiftUI

/// My position status board — takes the buy price/date and shows the return
/// against the current price. This is a plain factual calculation of "current
/// price minus buy price," not a judgment or prediction of whether it will
/// rise or fall going forward.
struct PositionCard: View {
    let ticker: String
    let currentPrice: Int?

    @EnvironmentObject private var positions: PositionStore

    @State private var priceInput = ""
    @State private var dateInput = Date()

    var body: some View {
        if let position = positions.position(for: ticker) {
            displayView(position)
        } else {
            inputForm
        }
    }

    private var inputForm: some View {
        CardContainer(title: "내 포지션", icon: "person.crop.circle.badge.plus") {
            VStack(alignment: .leading, spacing: 8) {
                Text("매수가와 매수일을 입력하면 현재가 대비 손익을 계산해 보여줍니다.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack(spacing: 8) {
                    TextField("매수가(원)", text: $priceInput)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 110)
                    DatePicker("", selection: $dateInput, in: ...Date(), displayedComponents: .date)
                        .labelsHidden()
                    Button("저장", action: save)
                        .buttonStyle(.borderedProminent)
                        .tint(Theme.accent)
                        .disabled(Double(priceInput) == nil)
                }
            }
        }
    }

    private func save() {
        guard let price = Double(priceInput), price > 0 else { return }
        positions.set(Position(buyPrice: price, buyDate: dateInput), for: ticker)
    }

    private func displayView(_ position: Position) -> some View {
        CardContainer(title: "내 포지션", icon: "person.crop.circle.fill") {
            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("매수가 \(Int(position.buyPrice).formatted())원")
                            .font(.caption)
                        Text("매수일 \(position.buyDate.formatted(date: .abbreviated, time: .omitted))")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button {
                        positions.clear(for: ticker)
                    } label: {
                        Image(systemName: "xmark.circle")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                    .help("포지션 삭제")
                }

                if let currentPrice {
                    let diff = Double(currentPrice) - position.buyPrice
                    let pct = diff / position.buyPrice * 100
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Text("\(diff >= 0 ? "+" : "")\(Int(diff).formatted())원")
                            .font(.title3.bold())
                            .monospacedDigit()
                            .foregroundStyle(Theme.changeColor(pct))
                        ChangeBadge(pct: pct)
                    }
                    Text("현재가(\(currentPrice.formatted())원) - 매수가 기준 단순 계산입니다.")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                } else {
                    ProgressView().controlSize(.small)
                }
            }
        }
    }
}

/// Card showing statistics on similar past drop-and-recovery episodes.
/// StockDetailView attaches this view only conditionally, when the price is
/// currently below the buy price — it isn't shown at all while it's up.
struct RecoveryHistoryCard: View {
    let ticker: String
    let buyPrice: Double

    @State private var state: LoadState<RecoveryHistoryResponse> = .loading

    var body: some View {
        CardContainer(title: "과거 유사 하락 사례 (참고용)", icon: "clock.arrow.circlepath") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 6) {
                        Text(data.summary).font(.callout)
                        if data.sufficientSample {
                            Text(
                                "표본 \(data.sampleCount)건"
                                + (data.unresolvedCount > 0 ? " · 아직 회복 안 한 사례 \(data.unresolvedCount)건은 평균에서 제외" : "")
                            )
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        }
                        Text(data.disclaimer)
                            .font(.caption2.bold())
                            .foregroundStyle(.orange)
                    }
                )
            }
        }
        .task(id: "\(ticker):\(buyPrice)") {
            do {
                state = .loaded(try await APIClient.shared.recoveryHistory(ticker, buyPrice: buyPrice))
            } catch {
                state = .failed(error.localizedDescription)
            }
        }
    }
}
