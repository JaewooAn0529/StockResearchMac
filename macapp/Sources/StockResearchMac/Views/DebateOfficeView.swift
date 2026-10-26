import SwiftUI

/// After the debate result arrives (the backend sends it all at once), this plays
/// it back visual-novel style, as if the 8 participants were "speaking" in turn.
/// Characters/backgrounds are made with a local pixel-art SD model — see
/// assets-gen/generate_batch.py. This is staged: not real-time streaming, but a
/// dramatization that reconstructs the turn order "as if" it were live.
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
                out.append(Turn(key: "bull-\(round.round)", name: "\(bull.name) · Round \(round.round)", image: bull.image, text: round.bull, accent: bull.accent))
            }
            if let bear = roster["bear"] {
                out.append(Turn(key: "bear-\(round.round)", name: "\(bear.name) · Round \(round.round)", image: bear.image, text: round.bear, accent: bear.accent))
            }
        }
        if let trader = roster["trader"] {
            out.append(Turn(key: "trader", name: trader.name, image: trader.image, text: "[\(data.decision.decision)] " + data.decision.rationale, accent: trader.accent))
        }
        if let risk = roster["risk"] {
            let text = data.riskReview.concern.isEmpty ? "\(data.riskReview.verdict) — no concerns" : data.riskReview.concern
            out.append(Turn(key: "risk", name: risk.name, image: risk.image, text: text, accent: risk.accent))
        }
        return out
    }

    var body: some View {
        VStack(spacing: 0) {
            ZStack(alignment: .bottom) {
                // Reuse the same tile-based office as the home screen for the background
                // (a single monolithic background image isn't used because its pixels stretch when the size changes)
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

    /// Lines up full-body sprites as if standing on the office floor, and makes
    /// only the currently speaking character bigger and bounce up and down to
    /// show "this person is talking right now."
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
                Button(revealed ? "Replay" : "Skip") {
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
                .id(turnIndex)  // so the transition re-triggers whenever the dialogue changes
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
            // Give dwell time proportional to the dialogue length, but clamp it so it's never too long or too short
            let seconds = min(max(Double(turns[i].text.count) / 28.0, 2.2), 6.0)
            try? await Task.sleep(for: .seconds(seconds))
        }
        if !Task.isCancelled {
            revealed = true
        }
    }
}
