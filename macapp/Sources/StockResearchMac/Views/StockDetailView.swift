import SwiftUI

struct StockDetailView: View {
    let ticker: String

    @EnvironmentObject private var favorites: FavoritesStore
    @EnvironmentObject private var positions: PositionStore

    @State private var priceState: LoadState<PriceResponse> = .loading
    @State private var flowsState: LoadState<FlowsResponse> = .loading
    @State private var valuationState: LoadState<ValuationResponse> = .loading
    @State private var consensusState: LoadState<ConsensusResponse> = .loading
    @State private var technicalState: LoadState<TechnicalResponse> = .loading
    @State private var volatilityState: LoadState<VolatilityResponse> = .loading
    @State private var rsiSignalStatsState: LoadState<RsiSignalStatsResponse> = .loading
    @State private var peersState: LoadState<PeerComparisonResponse> = .loading
    @State private var earningsState: LoadState<EarningsCalendarResponse> = .loading
    @State private var riskState: LoadState<RiskFlagsResponse> = .loading
    @State private var newsState: LoadState<NewsResponse> = .loading
    @State private var favoriteBounce = false

    private let cardColumns = [GridItem(.adaptive(minimum: 260), spacing: 12)]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                header

                if case .loaded(let price) = priceState {
                    PriceChartView(ohlcv: price.ohlcv)
                        .transition(.opacity.combined(with: .scale(scale: 0.98, anchor: .top)))
                }

                PositionCard(ticker: ticker, currentPrice: currentPriceValue)
                if let position = positions.position(for: ticker),
                   let cp = currentPriceValue,
                   Double(cp) < position.buyPrice {
                    RecoveryHistoryCard(ticker: ticker, buyPrice: position.buyPrice)
                }

                NavigationLink(value: DebateRoute(ticker: ticker)) {
                    Label("멀티에이전트 토론 시작", systemImage: "bubble.left.and.bubble.right")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                }
                .buttonStyle(.borderedProminent)
                .tint(Theme.accent)

                SectionHeader(title: "지표", icon: "square.grid.2x2.fill")
                LazyVGrid(columns: cardColumns, spacing: 12) {
                    FlowCard(state: flowsState)
                    ValuationCard(state: valuationState)
                    ConsensusCard(state: consensusState)
                    TechnicalCard(state: technicalState)
                    VolatilityCard(state: volatilityState)
                    RsiSignalStatsCard(state: rsiSignalStatsState)
                    PeersCard(state: peersState)
                    EarningsCalendarCard(state: earningsState)
                    RiskFlagsCard(state: riskState)
                }

                NewsListView(state: newsState)

                Text("이 정보는 투자 판단을 돕기 위한 참고 자료이며, 투자 판단과 그 책임은 본인에게 있습니다.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .padding()
            .animation(.spring(response: 0.4, dampingFraction: 0.82), value: currentPriceValue)
        }
        .navigationTitle(displayName)
        .toolbar {
            ToolbarItem {
                Button {
                    toggleFavorite()
                    favoriteBounce.toggle()
                } label: {
                    Image(systemName: favorites.contains(ticker) ? "star.fill" : "star")
                        .symbolEffect(.bounce, value: favoriteBounce)
                }
            }
        }
        .task(id: ticker) {
            resetStates()
            Task { await loadPrice() }
            Task { await loadFlows() }
            Task { await loadValuation() }
            Task { await loadConsensus() }
            Task { await loadTechnical() }
            Task { await loadVolatility() }
            Task { await loadRsiSignalStats() }
            Task { await loadPeers() }
            Task { await loadEarnings() }
            Task { await loadRisk() }
            Task { await loadNews() }
        }
    }

    private var displayName: String {
        if case .loaded(let price) = priceState { return price.name }
        return ticker
    }

    private var currentPriceValue: Int? {
        if case .loaded(let price) = priceState { return price.currentPrice }
        return nil
    }

    private var header: some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            StockLogoView(ticker: ticker, size: 44)
            Text(displayName).font(.largeTitle.bold())
            if case .loaded(let price) = priceState {
                Text("\(price.currentPrice.formatted())원")
                    .font(.title2)
                    .monospacedDigit()
                    .contentTransition(.numericText())
                    .foregroundStyle(.secondary)
                ChangeBadge(pct: price.changePct)
            }
            Spacer()
        }
    }

    private func resetStates() {
        priceState = .loading
        flowsState = .loading
        valuationState = .loading
        consensusState = .loading
        technicalState = .loading
        volatilityState = .loading
        rsiSignalStatsState = .loading
        peersState = .loading
        earningsState = .loading
        riskState = .loading
        newsState = .loading
    }

    // Loads each of the 10 indicators independently — if one fails, the other
    // cards still display normally (the same philosophy as the backend's orchestrator.gather_data).
    private func loadPrice() async {
        do { priceState = .loaded(try await APIClient.shared.price(ticker)) }
        catch { priceState = .failed(error.localizedDescription) }
    }
    private func loadFlows() async {
        do { flowsState = .loaded(try await APIClient.shared.flows(ticker)) }
        catch { flowsState = .failed(error.localizedDescription) }
    }
    private func loadValuation() async {
        do { valuationState = .loaded(try await APIClient.shared.valuation(ticker)) }
        catch { valuationState = .failed(error.localizedDescription) }
    }
    private func loadConsensus() async {
        do { consensusState = .loaded(try await APIClient.shared.consensus(ticker)) }
        catch { consensusState = .failed(error.localizedDescription) }
    }
    private func loadTechnical() async {
        do { technicalState = .loaded(try await APIClient.shared.technical(ticker)) }
        catch { technicalState = .failed(error.localizedDescription) }
    }
    private func loadVolatility() async {
        do { volatilityState = .loaded(try await APIClient.shared.volatility(ticker)) }
        catch { volatilityState = .failed(error.localizedDescription) }
    }
    private func loadRsiSignalStats() async {
        do { rsiSignalStatsState = .loaded(try await APIClient.shared.rsiSignalStats(ticker)) }
        catch { rsiSignalStatsState = .failed(error.localizedDescription) }
    }
    private func loadPeers() async {
        do { peersState = .loaded(try await APIClient.shared.peers(ticker)) }
        catch { peersState = .failed(error.localizedDescription) }
    }
    private func loadEarnings() async {
        do { earningsState = .loaded(try await APIClient.shared.earningsCalendar(ticker)) }
        catch { earningsState = .failed(error.localizedDescription) }
    }
    private func loadRisk() async {
        do { riskState = .loaded(try await APIClient.shared.riskFlags(ticker)) }
        catch { riskState = .failed(error.localizedDescription) }
    }
    private func loadNews() async {
        do { newsState = .loaded(try await APIClient.shared.news(ticker)) }
        catch { newsState = .failed(error.localizedDescription) }
    }

    private func toggleFavorite() {
        Task {
            if favorites.contains(ticker) {
                favorites.toggle(SearchResult(ticker: ticker, name: displayName, market: ""))
            } else if let result = try? await APIClient.shared.search(query: ticker).first(where: { $0.ticker == ticker }) {
                favorites.toggle(result)
            }
        }
    }
}
