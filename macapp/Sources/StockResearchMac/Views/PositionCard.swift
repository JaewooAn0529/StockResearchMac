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
        CardContainer(title: "My position", icon: "person.crop.circle.badge.plus") {
            VStack(alignment: .leading, spacing: 8) {
                Text("Enter your purchase price and date to see your profit/loss against the current price.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack(spacing: 8) {
                    TextField("Purchase price (₩)", text: $priceInput)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 110)
                    DatePicker("", selection: $dateInput, in: ...Date(), displayedComponents: .date)
                        .labelsHidden()
                    Button("Save", action: save)
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
        CardContainer(title: "My position", icon: "person.crop.circle.fill") {
            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Bought at ₩\(Int(position.buyPrice).formatted())")
                            .font(.caption)
                        Text("Bought on \(position.buyDate.formatted(date: .abbreviated, time: .omitted))")
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
                    .help("Delete position")
                }

                if let currentPrice {
                    let diff = Double(currentPrice) - position.buyPrice
                    let pct = diff / position.buyPrice * 100
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Text("\(diff >= 0 ? "+" : "")₩\(Int(diff).formatted())")
                            .font(.title3.bold())
                            .monospacedDigit()
                            .foregroundStyle(Theme.changeColor(pct))
                        ChangeBadge(pct: pct)
                    }
                    Text("A simple calculation: current price (₩\(currentPrice.formatted())) minus purchase price.")
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
        CardContainer(title: "Similar past drawdowns (reference only)", icon: "clock.arrow.circlepath") {
            CardStateView(state: state) { data in
                AnyView(
                    VStack(alignment: .leading, spacing: 6) {
                        Text(data.summary).font(.callout)
                        if data.sufficientSample {
                            Text(
                                "Sample: \(data.sampleCount) cases"
                                + (data.unresolvedCount > 0 ? " · \(data.unresolvedCount) not-yet-recovered cases excluded from the average" : "")
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
