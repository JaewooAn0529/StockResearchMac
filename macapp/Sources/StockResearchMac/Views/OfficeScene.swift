import SwiftUI

/// 오피스에서 실제로 걸어다니는 캐릭터 한 명의 상태.
/// 자기 책상과 순회 지점 사이를 오가면서, 책상에서는 앉아서 일하고
/// 밖에서는 커피를 마시거나 통화를 한다.
@MainActor
final class OfficeActor: ObservableObject, Identifiable {
    enum Mode {
        case working    // 책상에 앉아 타이핑
        case walking    // 이동 중
        case idling     // 서서 잡담/커피
    }

    let id: String
    let displayName: String
    let desk: CGPoint          // 자기 자리 (0~1 정규화)

    @Published var position: CGPoint
    @Published var mode: Mode = .working
    @Published var facingLeft = false
    @Published var animFrame = 0        // 걷기/타이핑 프레임 토글
    @Published var emote: String?       // 말풍선 아이콘

    init(id: String, displayName: String, desk: CGPoint) {
        self.id = id
        self.displayName = displayName
        self.desk = desk
        self.position = desk
    }

    /// 현재 상태에 맞는 스프라이트 프레임 이름.
    /// 프레임은 pixel-agents(MIT) 스프라이트 시트에서 잘라낸 것 —
    /// assets-gen/slice_sprites.py 참고.
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

/// 픽셀아트 오피스. 바닥 타일을 깔고 가구를 배치한 뒤 그 위에서 캐릭터들이
/// 자기 책상과 휴게 공간 사이를 오간다.
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
                                    // 배경이 ignoresSafeArea로 타이틀바 아래까지 깔리므로,
                                    // 말풍선이 타이틀바에 가려지지 않게 위쪽 여유를 넉넉히 둔다
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

/// 바닥 타일 + 벽 + 가구로 방을 조립한다. 통짜 배경 이미지 대신 타일을 깔면
/// 어떤 창 크기에서도 픽셀이 늘어나지 않고 선명하게 유지된다.
struct OfficeRoomBackdrop: View {
    let size: CGSize

    private let tile: CGFloat = 48

    var body: some View {
        ZStack(alignment: .topLeading) {
            Color(red: 0.14, green: 0.13, blue: 0.17)

            // 바닥 타일
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

            // 벽 (상단 띠). wall_wall_0.png는 단일 이미지가 아니라 32x32 타일 8개가
            // 든 타일셋이라, 통째로 늘려 깔면 줄무늬처럼 깨진다(실제로 겪음).
            // 그래서 민무늬 벽 타일 하나만 잘라낸 wall_plain.png를 정사각 비율로 반복한다.
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

            // 벽과 바닥 경계에 걸레받이 라인을 넣어 평면이 아니라 방처럼 보이게
            Rectangle()
                .fill(Color.black.opacity(0.35))
                .frame(width: size.width, height: 3)
                .offset(y: tile * 2)

            // 가구 배치 — 책상은 캐릭터 자리와 맞춰둔다
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

            // 켜져 있는 PC — 3프레임을 순환시켜 모니터가 깜빡이게
            TimelineView(.animation(minimumInterval: 0.45)) { timeline in
                let step = Int(timeline.date.timeIntervalSinceReferenceDate / 0.45) % 3 + 1
                Group {
                    furniture("furn_PC_FRONT_ON_\(step)", x: 0.10, y: 0.47, w: 40)
                    furniture("furn_PC_FRONT_ON_\((step % 3) + 1)", x: 0.32, y: 0.47, w: 40)
                    furniture("furn_PC_FRONT_ON_\(((step + 1) % 3) + 1)", x: 0.56, y: 0.47, w: 40)
                    furniture("furn_PC_FRONT_ON_\(step)", x: 0.80, y: 0.47, w: 40)
                }
            }

            // 창문에서 들어오는 햇살이 아주 천천히 밝아졌다 어두워진다
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

/// 캐릭터들의 하루를 굴리는 루프. 각자 독립 Task로 돌아 서로 다른 타이밍에 움직인다.
@MainActor
private final class OfficeDirector: ObservableObject {
    @Published private(set) var actors: [OfficeActor] = []
    private var tasks: [Task<Void, Never>] = []

    // 책상 자리 (OfficeRoom의 책상 배치와 맞춤)
    private let desks: [CGPoint] = [
        CGPoint(x: 0.10, y: 0.44), CGPoint(x: 0.32, y: 0.44),
        CGPoint(x: 0.56, y: 0.44), CGPoint(x: 0.80, y: 0.44),
        CGPoint(x: 0.10, y: 0.72), CGPoint(x: 0.32, y: 0.72),
        CGPoint(x: 0.56, y: 0.72), CGPoint(x: 0.80, y: 0.72),
    ]

    // 휴게 공간(소파/커피/화이트보드 근처) — 자리를 뜰 때 가는 곳
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
        // 타이핑/걷기 프레임 토글은 계속 돌린다
        let animTask = Task { @MainActor in
            while !Task.isCancelled {
                actor.animFrame = actor.animFrame == 0 ? 1 : 0
                try? await Task.sleep(for: .milliseconds(actor.mode == .walking ? 260 : 700))
            }
        }
        defer { animTask.cancel() }

        while !Task.isCancelled {
            // 1) 책상에서 일한다
            actor.mode = .working
            withAnimation(.spring(response: 0.3)) { actor.emote = "keyboard.fill" }
            try? await Task.sleep(for: .seconds(.random(in: 6...14)))
            withAnimation(.easeOut(duration: 0.3)) { actor.emote = nil }
            guard !Task.isCancelled else { return }

            // 2) 휴게 공간으로 걸어간다
            let spot = hangouts.randomElement() ?? actor.desk
            await walk(actor, to: spot)
            guard !Task.isCancelled else { return }

            // 3) 잠깐 쉰다 (커피/통화/잡담)
            actor.mode = .idling
            withAnimation(.spring(response: 0.3)) {
                actor.emote = ["cup.and.saucer.fill", "phone.fill", "bubble.left.fill", "smoke.fill"].randomElement()
            }
            try? await Task.sleep(for: .seconds(.random(in: 4...9)))
            withAnimation(.easeOut(duration: 0.3)) { actor.emote = nil }
            guard !Task.isCancelled else { return }

            // 4) 자기 자리로 돌아간다
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
