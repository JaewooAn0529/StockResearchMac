import SwiftUI

/// 토론 결과를 받은 뒤(백엔드는 한 번에 다 준다) 8명이 순서대로 "말하는" 것처럼
/// 비주얼노벨 스타일로 재생(연출)한다. 로컬 픽셀아트 SD 모델로 만든 캐릭터/배경을
/// 쓴다 — assets-gen/generate_batch.py 참고. 진짜 실시간 스트리밍이 아니라
/// "가상으로" 순서를 재현하는 연출이라는 걸 전제로 한다.
private struct Turn {
    let key: String
    let name: String
    let image: String
    let text: String
    let accent: Color
}

private let roster = pixelCharacterRoster

struct DebateOfficeView: View {
    let data: DebateAnalysisResponse

    @State private var turnIndex = 0
    @State private var revealed = false
    @State private var playbackTask: Task<Void, Never>?

    private var turns: [Turn] {
        var out: [Turn] = []
        for key in ["fundamentals", "news", "technical", "flow"] {
            guard let info = roster[key], let text = data.analystReports[key] else { continue }
            out.append(Turn(key: key, name: info.name, image: info.image, text: text, accent: info.accent))
        }
        for round in data.debateRounds {
            if let bull = roster["bull"] {
                out.append(Turn(key: "bull-\(round.round)", name: "\(bull.name) · \(round.round)라운드", image: bull.image, text: round.bull, accent: bull.accent))
            }
            if let bear = roster["bear"] {
                out.append(Turn(key: "bear-\(round.round)", name: "\(bear.name) · \(round.round)라운드", image: bear.image, text: round.bear, accent: bear.accent))
            }
        }
        if let trader = roster["trader"] {
            out.append(Turn(key: "trader", name: trader.name, image: trader.image, text: "[\(data.decision.decision)] " + data.decision.rationale, accent: trader.accent))
        }
        if let risk = roster["risk"] {
            let text = data.riskReview.concern.isEmpty ? "\(data.riskReview.verdict) — 특이사항 없음" : data.riskReview.concern
            out.append(Turn(key: "risk", name: risk.name, image: risk.image, text: text, accent: risk.accent))
        }
        return out
    }

    var body: some View {
        VStack(spacing: 0) {
            ZStack(alignment: .bottom) {
                // 홈 화면과 같은 타일 기반 오피스를 배경으로 재사용한다
                // (통짜 배경 이미지는 크기가 바뀌면 픽셀이 늘어나서 안 쓴다)
                GeometryReader { geo in
                    OfficeRoomBackdrop(size: geo.size)
                }
                .frame(height: 240)
                .clipped()

                castRow
                    .padding(.bottom, 6)
            }
            .frame(height: 240)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

            dialogueBox
        }
        .task {
            playbackTask = Task { await playback() }
        }
        .onDisappear {
            playbackTask?.cancel()
        }
    }

    /// 전신 스프라이트를 오피스 바닥에 세워둔 것처럼 늘어놓고, 말하는 차례인
    /// 캐릭터만 크게 + 위아래로 통통 튀게 해서 "지금 이 사람이 말한다"를 보여준다.
    private var castRow: some View {
        TimelineView(.animation) { timeline in
            let t = timeline.date.timeIntervalSinceReferenceDate
            HStack(alignment: .bottom, spacing: 4) {
                ForEach(Array(turns.enumerated()), id: \.offset) { idx, turn in
                    let isActive = idx == turnIndex
                    let hasSpoken = idx <= turnIndex || revealed
                    let bounce = isActive ? CGFloat(sin(t * 6)) * 4 : 0

                    pixelImage(turn.image)
                        .resizable()
                        .interpolation(.none)
                        .aspectRatio(contentMode: .fit)
                        .frame(width: isActive ? 92 : 58, height: isActive ? 92 : 58)
                        .offset(y: bounce)
                        .opacity(hasSpoken ? 1 : 0.4)
                        .shadow(color: isActive ? turn.accent.opacity(0.8) : .black.opacity(0.3), radius: isActive ? 10 : 3, y: 3)
                        .animation(.spring(response: 0.35, dampingFraction: 0.7), value: turnIndex)
                }
            }
        }
    }

    private var dialogueBox: some View {
        let turn = turns.indices.contains(turnIndex) ? turns[turnIndex] : nil

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                if let turn {
                    Text(turn.name)
                        .font(.subheadline.bold())
                        .foregroundStyle(turn.accent)
                }
                Spacer()
                Text("\(min(turnIndex + 1, turns.count)) / \(turns.count)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Button(revealed ? "다시보기" : "건너뛰기") {
                    if revealed {
                        playbackTask?.cancel()
                        turnIndex = 0
                        revealed = false
                        playbackTask = Task { await playback() }
                    } else {
                        playbackTask?.cancel()
                        revealed = true
                        turnIndex = max(turns.count - 1, 0)
                    }
                }
                .font(.caption)
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
            Text(turn?.text ?? "")
                .font(.callout)
                .id(turnIndex)  // 대사 바뀔 때 트랜지션이 새로 타게
                .transition(.opacity)
                .animation(.easeInOut(duration: 0.25), value: turnIndex)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(Color(nsColor: .controlBackgroundColor)))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Color.primary.opacity(0.08), lineWidth: 1))
        .padding(.top, 10)
    }

    private func playback() async {
        for i in turns.indices {
            if Task.isCancelled { return }
            turnIndex = i
            // 대사 길이에 비례해서 머무는 시간을 주되, 너무 길게/짧게 가진 않게 범위를 둔다
            let seconds = min(max(Double(turns[i].text.count) / 28.0, 2.2), 6.0)
            try? await Task.sleep(for: .seconds(seconds))
        }
        if !Task.isCancelled {
            revealed = true
        }
    }
}
