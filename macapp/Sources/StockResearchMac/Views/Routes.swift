import Foundation

/// NavigationStack's navigationDestination(for:) maps only one destination per
/// value type, so to distinguish "ticker going to stock detail" from "ticker
/// going to debate view" we use separate dedicated types instead of a bare String.
struct StockRoute: Hashable {
    let ticker: String
}

struct DebateRoute: Hashable {
    let ticker: String
}

/// The past decision history screen (no arguments)
struct HistoryRoute: Hashable {}
