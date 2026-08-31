"""생성된 스프라이트의 배경을 투명화한다.

flood-fill 방식은 배경에 미세한 세로줄/격자 노이즈가 있으면 연결이 끊겨서
못 퍼진다(실측: technical은 2%만 지워졌다). 그래서 "배경색과 비슷한 픽셀"을
전부 후보로 잡은 뒤, 캐릭터 실루엣(가장 큰 비배경 덩어리)만 남기고 나머지를
지우는 방식으로 바꿨다.

캐릭터 내부의 흰 셔츠처럼 배경색과 비슷한 색도, 실루엣 안에 갇혀 있으면
(=바깥과 연결되지 않으면) 살린다 — 실루엣 내부 구멍 메우기로 처리.
"""

import glob
from collections import deque

from PIL import Image

TOLERANCE = 60


def transparent_background(path: str) -> None:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()

    # 테두리 픽셀들의 최빈색을 배경색으로 본다 (모서리 4개보다 노이즈에 강함)
    border = []
    for x in range(w):
        border.append(px[x, 0][:3])
        border.append(px[x, h - 1][:3])
    for y in range(h):
        border.append(px[0, y][:3])
        border.append(px[w - 1, y][:3])
    bg_r = sorted(c[0] for c in border)[len(border) // 2]
    bg_g = sorted(c[1] for c in border)[len(border) // 2]
    bg_b = sorted(c[2] for c in border)[len(border) // 2]

    def is_bg(p):
        return (
            abs(p[0] - bg_r) <= TOLERANCE
            and abs(p[1] - bg_g) <= TOLERANCE
            and abs(p[2] - bg_b) <= TOLERANCE
        )

    # 1) 비배경(=캐릭터 후보) 마스크
    fg = [[not is_bg(px[x, y]) for x in range(w)] for y in range(h)]

    # 2) 가장 큰 연결 덩어리만 캐릭터로 인정 (배경 노이즈 점들 제거)
    seen = [[False] * w for _ in range(h)]
    best_component: list[tuple[int, int]] = []
    for sy in range(h):
        for sx in range(w):
            if not fg[sy][sx] or seen[sy][sx]:
                continue
            comp = []
            q = deque([(sx, sy)])
            seen[sy][sx] = True
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and fg[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if len(comp) > len(best_component):
                best_component = comp

    keep = [[False] * w for _ in range(h)]
    for x, y in best_component:
        keep[y][x] = True

    # 3) 실루엣 내부의 구멍(셔츠 등 배경색과 비슷한 부분)을 메운다:
    #    테두리에서 flood-fill로 "바깥"을 찾고, 바깥이 아니면 캐릭터로 친다
    outside = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not keep[y][x] and not outside[y][x]:
                outside[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not keep[y][x] and not outside[y][x]:
                outside[y][x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not keep[ny][nx] and not outside[ny][nx]:
                outside[ny][nx] = True
                q.append((nx, ny))

    cleared = 0
    for y in range(h):
        for x in range(w):
            if outside[y][x]:
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, 0)
                cleared += 1

    img.save(path)
    print(f"{path}: bg=rgb({bg_r},{bg_g},{bg_b}), {cleared / (w * h) * 100:.0f}% 투명화")


if __name__ == "__main__":
    for path in sorted(glob.glob("sprite_*.png")):
        if "background" in path:
            continue  # 오피스 배경은 투명화하면 안 된다
        transparent_background(path)
    print("완료")
