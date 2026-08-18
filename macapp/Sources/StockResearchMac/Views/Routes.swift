import Foundation

/// NavigationStack의 navigationDestination(for:)는 값 타입별로 목적지가 하나씩만
/// 매핑되므로, "종목상세로 가는 티커"와 "토론뷰로 가는 티커"를 구분하려고
/// bare String 대신 각각 별도 타입을 쓴다.
struct StockRoute: Hashable {
    let ticker: String
}

struct DebateRoute: Hashable {
    let ticker: String
}

/// 지난 판단 기록 화면 (인자 없음)
struct HistoryRoute: Hashable {}
