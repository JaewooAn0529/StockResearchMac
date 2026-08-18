import AppKit
import SwiftUI

/// `swift run`으로 띄운 프로세스는 제대로 된 .app 번들(더블클릭 실행)이 아니라서
/// 창은 뜨는데 키보드 포커스를 자동으로 못 가져온다 — 검색창에 타이핑이 안 되는
/// 증상이 바로 이것. 명시적으로 activate를 호출해서 강제로 최전면·포커스를 가져온다.
final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
}

@main
struct StockResearchMacApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var favorites = FavoritesStore()
    @StateObject private var positions = PositionStore()

    var body: some Scene {
        WindowGroup {
            HomeView()
                .environmentObject(favorites)
                .environmentObject(positions)
                .frame(minWidth: 700, minHeight: 500)
        }
    }
}
