"""Slices pixel-agents (MIT) character sprite sheets into individual frame PNGs.

The sprites we generated directly with AI had background noise and character
inconsistency between frames, so we're replacing them with vetted assets drawn
by a professional pixel artist.
Source: https://github.com/pixel-agents-hq/pixel-agents (MIT, Pablo De Lucca)
Original art: JIK-A-4, Metro City

Sheet spec: 112x96, a 16x32 frame grid = 7 columns x 3 rows.
Row 0: front (down) walk/stand + sit, row 1: back (up), row 2: side (right)
"""

import os

from PIL import Image

SRC_DIR = "/private/tmp/claude-501/-Users-jaewooan-AIstocktrading/2973cf70-02b3-419a-9f35-40c105fe99b4/scratchpad/pixel-agents/webview-ui/public/assets"
DEST_DIR = "/Users/jaewooan/AIstocktrading/stock-research-app/macapp/Sources/StockResearchMac/Resources"

FRAME_W, FRAME_H = 16, 32
SCALE = 6  # Nearest-neighbor upscale — keeps pixels crisp even at large display size

# Assigns the 6 sheet variants to our app's 8 characters (only 6 exist, so 2 characters reuse one).
CHARACTER_SHEETS = {
    "fundamentals": "char_0",
    "news": "char_1",
    "technical": "char_2",
    "flow": "char_3",
    "bull": "char_4",
    "bear": "char_5",
    "trader": "char_0",
    "risk": "char_2",
}

# (row, col) -> the name we use. Walking alternates between 2 frames.
FRAMES = {
    "idle": (0, 0),      # Front standing
    "walk1": (0, 1),     # Front walk A
    "walk2": (0, 2),     # Front walk B
    "sit": (0, 5),       # Sitting
    "work": (0, 6),      # Looking at documents/working
    "side1": (2, 0),     # Side walk A
    "side2": (2, 1),     # Side walk B
}


def main() -> None:
    os.makedirs(DEST_DIR, exist_ok=True)

    # Clean up: the previously AI-generated sprites are no longer used
    for old in os.listdir(DEST_DIR):
        if old.startswith("sprite_") and old.endswith(".png"):
            os.remove(os.path.join(DEST_DIR, old))

    for char_key, sheet_name in CHARACTER_SHEETS.items():
        sheet = Image.open(f"{SRC_DIR}/characters/{sheet_name}.png").convert("RGBA")
        for frame_name, (row, col) in FRAMES.items():
            box = (col * FRAME_W, row * FRAME_H, (col + 1) * FRAME_W, (row + 1) * FRAME_H)
            frame = sheet.crop(box)
            frame = frame.resize((FRAME_W * SCALE, FRAME_H * SCALE), Image.NEAREST)
            frame.save(f"{DEST_DIR}/sprite_{char_key}_{frame_name}.png")
        print(f"{char_key} ({sheet_name}): {len(FRAMES)}프레임")

    # Also pull in floor tiles and furniture so the office background can be assembled directly
    for floor in sorted(os.listdir(f"{SRC_DIR}/floors"))[:3]:
        if floor.endswith(".png"):
            img = Image.open(f"{SRC_DIR}/floors/{floor}").convert("RGBA")
            img.save(f"{DEST_DIR}/floor_{floor}")
            print(f"floor: {floor} {img.size}")

    for wall in sorted(os.listdir(f"{SRC_DIR}/walls")):
        if wall.endswith(".png"):
            img = Image.open(f"{SRC_DIR}/walls/{wall}").convert("RGBA")
            img.save(f"{DEST_DIR}/wall_{wall}")
            print(f"wall: {wall} {img.size}")

    # Furniture PNGs live inside per-name directories (e.g. DESK/DESK_FRONT.png).
    # PC has 3 "on" frames, so it can be used for a monitor-flicker animation.
    wanted_dirs = [
        "DESK", "WOODEN_CHAIR", "CUSHIONED_CHAIR", "PLANT", "PLANT_2", "LARGE_PLANT",
        "PC", "BOOKSHELF", "SOFA", "COFFEE", "CLOCK", "WHITEBOARD", "SMALL_PAINTING",
    ]
    copied = 0
    for d in wanted_dirs:
        src = f"{SRC_DIR}/furniture/{d}"
        if not os.path.isdir(src):
            continue
        for f in sorted(os.listdir(src)):
            if not f.endswith(".png"):
                continue
            img = Image.open(f"{src}/{f}").convert("RGBA")
            img.save(f"{DEST_DIR}/furn_{f}")
            copied += 1
    print(f"furniture: {copied}개 복사")


if __name__ == "__main__":
    main()
