import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var favorites: FavoritesStore

    @State private var searchText = ""
    @State private var searchResults: [SearchResult] = []
    @State private var searchTask: Task<Void, Never>?

    var body: some View {
        NavigationStack {
            ZStack {
                OfficeScene(favorites: favorites.items)

                if !searchText.isEmpty {
                    searchResultsList
                } else if favorites.items.isEmpty {
                    VStack {
                        Spacer()
                        Text("검색해서 관심종목을 추가하면 오피스 동료들 옆에 표시됩니다")
                            .font(.callout)
                            .foregroundStyle(.white)
                            .padding(10)
                            .background(.black.opacity(0.4), in: RoundedRectangle(cornerRadius: 10))
                        Spacer()
                    }
                    .allowsHitTesting(false)
                }
            }
            .navigationTitle("Stock Research")
            .navigationDestination(for: StockRoute.self) { route in
                StockDetailView(ticker: route.ticker)
            }
            .navigationDestination(for: DebateRoute.self) { route in
                DebateView(ticker: route.ticker)
            }
            .navigationDestination(for: HistoryRoute.self) { _ in
                DecisionHistoryView()
            }
            .toolbar {
                ToolbarItem {
                    NavigationLink(value: HistoryRoute()) {
                        Label("판단 기록", systemImage: "clock.arrow.circlepath")
                    }
                }
            }
            .searchable(text: $searchText, prompt: "종목명 또는 티커 검색")
            .onChange(of: searchText) { _, newValue in
                debounceSearch(newValue)
            }
        }
    }

    private var searchResultsList: some View {
        List(searchResults) { result in
            NavigationLink(value: StockRoute(ticker: result.ticker)) {
                StockCardView(result: result)
            }
            .buttonStyle(.plain)
            .listRowSeparator(.hidden)
            .listRowBackground(Color.clear)
        }
        .scrollContentBackground(.hidden)  // so the office scene behind shows through the list
    }

    private func debounceSearch(_ query: String) {
        searchTask?.cancel()
        guard !query.isEmpty else {
            searchResults = []
            return
        }
        searchTask = Task {
            try? await Task.sleep(for: .milliseconds(300))
            guard !Task.isCancelled else { return }
            do {
                searchResults = try await APIClient.shared.search(query: query)
            } catch {
                searchResults = []
            }
        }
    }
}
