"""Makes the background of generated sprites transparent.

The flood-fill approach breaks down when the background has faint vertical
line/grid noise, since the connection gets cut and it can't spread (measured:
only 2% got cleared for "technical"). So instead, we mark every pixel that's
"close to the background color" as a candidate, then keep only the character's
silhouette (the largest non-background blob) and erase the rest.

Colors similar to the background inside the character — like a white shirt —
are preserved as long as they're trapped inside the silhouette (i.e. not
connected to the outside) — handled by filling in the holes inside the silhouette.
"""

import glob
from collections import deque

from PIL import Image

TOLERANCE = 60


def transparent_background(path: str) -> None:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()

    # Treat the mode color of the border pixels as the background color (more noise-resistant than just the 4 corners)
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

    # 1) Non-background (= character candidate) mask
    fg = [[not is_bg(px[x, y]) for x in range(w)] for y in range(h)]

    # 2) Only accept the largest connected blob as the character (removes background noise specks)
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

    # 3) Fill in holes inside the silhouette (parts similar to the background color, like a shirt):
    #    flood-fill from the border to find the "outside," and treat anything that isn't outside as the character
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
            continue  # Don't make the office background transparent
        transparent_background(path)
    print("완료")
