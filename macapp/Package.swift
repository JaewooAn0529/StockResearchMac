// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "StockResearchMac",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "StockResearchMac",
            path: "Sources/StockResearchMac",
            resources: [.copy("Resources")]
        )
    ]
)
