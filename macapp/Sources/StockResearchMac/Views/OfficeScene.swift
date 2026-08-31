import SwiftUI

/// State for a single character actually walking around the office.
/// It moves back and forth between its own desk and rotating waypoints —
/// sitting and working at the desk, and drinking coffee or talking on the
/// phone when out and about.
@MainActor
final class OfficeActor: ObservableObject, Identifiable {
    enum Mode {
        case working    // seated at the desk, typing
        case walking    // moving
        case idling     // standing, chatting/coffee
    }

    let id: String
    let displayName: String
    let desk: CGPoint          // its own spot (normalized 0~1)

    @Published var position: CGPoint
    @Published var mode: Mode = .working
    @Published var facingLeft = false
    @Published var animFrame = 0        // toggles the walk/type animation frame
    @Published var emote: String?       // speech-bubble icon

    init(id: String, displayName: String, desk: CGPoint) {
        self.id = id
        self.displayName = displayName
        self.desk = desk
        self.position = desk
    }

    /// The sprite frame name matching the current state.
    /// Frames are cut from the pixel-agents (MIT) sprite sheet —
    /// see assets-gen/slice_sprites.py.
    var spriteName: String {
        switch mode {
        case .working:
            return "sprite_\(id)_\(animFrame == 0 ? "sit" : "work")"
        case .walking:
            return "sprite_\(id)_\(animFrame == 0 ? "walk1" : "walk2")"
        case .idling:
            return "sprite_\(id)_idle"
        }
    }
}

/// The pixel-art office. Floor tiles are laid, furniture is placed, and on top
/// of that the characters move between their own desks and the lounge area.
struct OfficeScene: View {
    let favorites: [SearchResult]
    var showBubbles: Bool = true

    @StateObject private var director = OfficeDirector()

    var body: some View {
        GeometryReader { geo in
            ZStack {
                OfficeRoomBackdrop(size: geo.size)
                    .allowsHitTesting(false)

                ForEach(director.actors) { actor in
                    ActorSprite(actor: actor)
                        .position(
                            x: geo.size.width * actor.position.x,
                            y: geo.size.height * actor.position.y
                        )
                }
                .allowsHitTesting(false)

                if showBubbles {
                    ForEach(Array(favorites.enumerated()), id: \.element.ticker) { idx, stock in
                        if idx < director.actors.count {
                            let actor = director.actors[idx]
                            StockBubble(result: stock)
                                .position(
                                    // The background extends under the title bar via ignoresSafeArea,
                                    // so leave generous top clearance so the bubble doesn't get hidden behind the title bar
                                    x: geo.size.width * actor.position.x,
                                    y: max(geo.size.height * actor.position.y - 68, 92)
                                )
                        }
                    }
                }
            }
            .frame(width: geo.size.width, height: geo.size.height)
            .onAppear { director.start() }
            .onDisappear { director.stop() }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .ignoresSafeArea()
    }
}

/// Assembles the room from floor tiles + walls + furniture. Using tiles instead
/// of a single monolithic background image keeps pixels crisp at any window
/// size instead of stretching.
struct OfficeRoomBackdrop: View {
    let size: CGSize

    private let tile: CGFloat = 48

    var body: some View {
        ZStack(alignment: .topLeading) {
            Color(red: 0.14, green: 0.13, blue: 0.17)

            // Floor tiles
            let cols = Int(ceil(size.width / tile))
            let rows = Int(ceil(size.height / tile))
            ForEach(0..<max(rows, 1), id: \.self) { r in
                ForEach(0..<max(cols, 1), id: \.self) { c in
                    pixelImage("floor_floor_0")
                        .resizable()
                        .interpolation(.none)
                        .frame(width: tile, height: tile)
                        .offset(x: CGFloat(c) * tile, y: CGFloat(r) * tile)
                }
            }

            // Wall (top band). wall_wall_0.png isn't a single image — it's a
            // tileset containing 8 32x32 tiles, so stretching it as one image
            // breaks into stripes (learned this the hard way). So instead we
            // repeat wall_plain.png, a single plain wall tile cut out at a
            // square aspect ratio.
            ForEach(0..<max(cols, 1), id: \.self) { c in
                VStack(spacing: 0) {
                    pixelImage("wall_plain")
                        .resizable()
                        .interpolation(.none)
                        .frame(width: tile, height: tile)
                    pixelImage("wall_plain")
                        .resizable()
                        .interpolation(.none)
                        .frame(width: tile, height: tile)
                }
                .offset(x: CGFloat(c) * tile, y: 0)
            }

            // Add a baseboard line at the wall/floor boundary so it reads as a room, not a flat plane
            Rectangle()
                .fill(Color.black.opacity(0.35))
                .frame(width: size.width, height: 3)
                .offset(y: tile * 2)

            // Furniture placement — desks are aligned with the character spots
            furniture("furn_DESK_FRONT", x: 0.10, y: 0.52, w: 96)
            furniture("furn_DESK_FRONT", x: 0.32, y: 0.52, w: 96)
            furniture("furn_DESK_FRONT", x: 0.56, y: 0.52, w: 96)
            furniture("furn_DESK_FRONT", x: 0.80, y: 0.52, w: 96)
            furniture("furn_DESK_FRONT", x: 0.10, y: 0.80, w: 96)
            furniture("furn_DESK_FRONT", x: 0.32, y: 0.80, w: 96)
            furniture("furn_DESK_FRONT", x: 0.56, y: 0.80, w: 96)
            furniture("furn_DESK_FRONT", x: 0.80, y: 0.80, w: 96)

            furniture("furn_LARGE_PLANT", x: 0.94, y: 0.30, w: 64)
            furniture("furn_PLANT", x: 0.03, y: 0.30, w: 48)
            furniture("furn_BOOKSHELF", x: 0.45, y: 0.22, w: 80)
            furniture("furn_WHITEBOARD", x: 0.68, y: 0.20, w: 80)
            furniture("furn_SOFA_FRONT", x: 0.20, y: 0.30, w: 96)
            furniture("furn_COFFEE", x: 0.30, y: 0.28, w: 32)

            // Powered-on PCs — cycle through 3 frames so the monitors flicker
            TimelineView(.animation(minimumInterval: 0.45)) { timeline in
                let step = Int(timeline.date.timeIntervalSinceReferenceDate / 0.45) % 3 + 1
                Group {
                    furniture("furn_PC_FRONT_ON_\(step)", x: 0.10, y: 0.47, w: 40)
                    furniture("furn_PC_FRONT_ON_\((step % 3) + 1)", x: 0.32, y: 0.47, w: 40)
                    furniture("furn_PC_FRONT_ON_\(((step + 1) % 3) + 1)", x: 0.56, y: 0.47, w: 40)
                    furniture("furn_PC_FRONT_ON_\(step)", x: 0.80, y: 0.47, w: 40)
                }
            }

            // Sunlight coming through the window very slowly brightens and dims
            TimelineView(.animation(minimumInterval: 0.1)) { timeline in
                let t = timeline.date.timeIntervalSinceReferenceDate
                LinearGradient(
                    colors: [Color.orange.opacity(0.16 + 0.05 * sin(t * 0.22)), .clear],
                    startPoint: .topTrailing, endPoint: .center
                )
            }

            LinearGradient(
                colors: [.clear, .clear, Color.black.opacity(0.35)],
                startPoint: .top, endPoint: .bottom
            )
        }
        .frame(width: size.width, height: size.height)
        .clipped()
    }

    private func furniture(_ name: String, x: CGFloat, y: CGFloat, w: CGFloat) -> some View {
        pixelImage(name)
            .resizable()
            .interpolation(.none)
            .aspectRatio(contentMode: .fit)
            .frame(width: w)
            .position(x: size.width * x, y: size.height * y)
    }
}

private struct ActorSprite: View {
    @ObservedObject var actor: OfficeActor

    var body: some View {
        ZStack(alignment: .top) {
            pixelImage(actor.spriteName)
                .resizable()
                .interpolation(.none)
                .aspectRatio(contentMode: .fit)
                .frame(width: 40, height: 80)
                .scaleEffect(x: actor.facingLeft ? -1 : 1, y: 1)
                .shadow(color: .black.opacity(0.4), radius: 2, y: 2)

            if let emote = actor.emote {
                Image(systemName: emote)
                    .font(.system(size: 10, weight: .bold))
                    .foregroundStyle(.black)
                    .padding(5)
                    .background(.white, in: Circle())
                    .offset(x: 20, y: -6)
                    .transition(.scale.combined(with: .opacity))
            }
        }
    }
}

/// The loop that runs the characters' day. Each runs as an independent Task, so they move on different timings.
@MainActor
private final class OfficeDirector: ObservableObject {
    @Published private(set) var actors: [OfficeActor] = []
    private var tasks: [Task<Void, Never>] = []

    // Desk spots (matched to the desk layout in OfficeRoom)
    private let desks: [CGPoint] = [
        CGPoint(x: 0.10, y: 0.44), CGPoint(x: 0.32, y: 0.44),
        CGPoint(x: 0.56, y: 0.44), CGPoint(x: 0.80, y: 0.44),
        CGPoint(x: 0.10, y: 0.72), CGPoint(x: 0.32, y: 0.72),
        CGPoint(x: 0.56, y: 0.72), CGPoint(x: 0.80, y: 0.72),
    ]

    // Lounge spots (near the sofa/coffee/whiteboard) — where they go when leaving their desk
    private let hangouts: [CGPoint] = [
        CGPoint(x: 0.22, y: 0.36), CGPoint(x: 0.31, y: 0.34),
        CGPoint(x: 0.68, y: 0.28), CGPoint(x: 0.46, y: 0.30),
        CGPoint(x: 0.90, y: 0.60),
    ]

    func start() {
        guard actors.isEmpty else { return }
        let keys = ["fundamentals", "news", "technical", "flow", "bull", "bear", "trader", "risk"]
        actors = keys.enumerated().map { idx, key in
            OfficeActor(
                id: key,
                displayName: pixelCharacterRoster[key]?.name ?? key,
                desk: desks[idx % desks.count]
            )
        }

        for (idx, actor) in actors.enumerated() {
            tasks.append(Task { [weak self] in
                try? await Task.sleep(for: .seconds(Double(idx) * 0.7))
                await self?.runLoop(for: actor)
            })
        }
    }

    func stop() {
        tasks.forEach { $0.cancel() }
        tasks.removeAll()
    }

    private func runLoop(for actor: OfficeActor) async {
        // Keep toggling the typing/walking animation frame continuously
        let animTask = Task { @MainActor in
            while !Task.isCancelled {
                actor.animFrame = actor.animFrame == 0 ? 1 : 0
                try? await Task.sleep(for: .milliseconds(actor.mode == .walking ? 260 : 700))
            }
        }
        defer { animTask.cancel() }

        while !Task.isCancelled {
            // 1) Work at the desk
            actor.mode = .working
            withAnimation(.spring(response: 0.3)) { actor.emote = "keyboard.fill" }
            try? await Task.sleep(for: .seconds(.random(in: 6...14)))
            withAnimation(.easeOut(duration: 0.3)) { actor.emote = nil }
            guard !Task.isCancelled else { return }

            // 2) Walk to the lounge area
            let spot = hangouts.randomElement() ?? actor.desk
            await walk(actor, to: spot)
            guard !Task.isCancelled else { return }

            // 3) Take a short break (coffee/phone call/chatting)
            actor.mode = .idling
            withAnimation(.spring(response: 0.3)) {
                actor.emote = ["cup.and.saucer.fill", "phone.fill", "bubble.left.fill", "smoke.fill"].randomElement()
            }
            try? await Task.sleep(for: .seconds(.random(in: 4...9)))
            withAnimation(.easeOut(duration: 0.3)) { actor.emote = nil }
            guard !Task.isCancelled else { return }

            // 4) Walk back to its own spot
            await walk(actor, to: actor.desk)
        }
    }

    private func walk(_ actor: OfficeActor, to target: CGPoint) async {
        let distance = hypot(target.x - actor.position.x, target.y - actor.position.y)
        let duration = max(Double(distance) * 7.0, 1.2)

        actor.facingLeft = target.x < actor.position.x
        actor.mode = .walking

        withAnimation(.linear(duration: duration)) {
            actor.position = target
        }
        try? await Task.sleep(for: .seconds(duration))
    }
}
