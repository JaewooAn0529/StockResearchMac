import AppKit
import SwiftUI

/// A process launched via `swift run` isn't a proper .app bundle (double-click
/// launched), so the window appears but doesn't automatically grab keyboard
/// focus — that's exactly why typing into the search field doesn't work. We
/// explicitly call activate to force it to the front and grab focus.
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
