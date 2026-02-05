// swift-tools-version: 5.9
// MrLiou Xcode Connector Package
// origin_signature: MrLiouWord

import PackageDescription

let package = Package(
    name: "MrLiouConnector",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(
            name: "MrLiouConnector",
            targets: ["MrLiouConnector"]
        ),
    ],
    dependencies: [
        // 無外部依賴，純 Swift 實現
    ],
    targets: [
        .target(
            name: "MrLiouConnector",
            dependencies: [],
            path: "Sources",
            swiftSettings: [
                .define("MRLIOU_ORIGIN", .when(configuration: .debug)),
            ]
        ),
        .testTarget(
            name: "MrLiouConnectorTests",
            dependencies: ["MrLiouConnector"],
            path: "Tests"
        ),
    ]
)
