"""pixel-agents(MIT)의 캐릭터 스프라이트 시트를 개별 프레임 PNG로 잘라낸다.

AI로 직접 생성한 스프라이트는 배경 노이즈/프레임 간 캐릭터 불일치 문제가 있어서,
프로 픽셀아티스트가 그린 검증된 에셋으로 교체한다.
출처: https://github.com/pixel-agents-hq/pixel-agents (MIT, Pablo De Lucca)
원작 아트: JIK-A-4, Metro City

시트 규격: 112x96, 16x32 프레임 격자 = 7열 x 3행.
행 0: 정면(down) 걷기/서기 + 앉기, 행 1: 뒷모습(up), 행 2: 측면(right)
"""

import os

from PIL import Image

SRC_DIR = "/private/tmp/claude-501/-Users-jaewooan-AIstocktrading/2973cf70-02b3-419a-9f35-40c105fe99b4/scratchpad/pixel-agents/webview-ui/public/assets"
DEST_DIR = "/Users/jaewooan/AIstocktrading/stock-research-app/macapp/Sources/StockResearchMac/Resources"

FRAME_W, FRAME_H = 16, 32
SCALE = 6  # nearest 확대 — 화면에서 크게 써도 픽셀이 또렷하게 유지된다

# 우리 앱의 캐릭터 8명에게 시트 6종을 배정한다(6종뿐이라 2명은 재사용).
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

# (행, 열) -> 우리가 쓸 이름. 걷기는 2프레임을 번갈아 쓴다.
FRAMES = {
    "idle": (0, 0),      # 정면 서기
    "walk1": (0, 1),     # 정면 걷기 A
    "walk2": (0, 2),     # 정면 걷기 B
    "sit": (0, 5),       # 앉아 있기
    "work": (0, 6),      # 서류 보기/작업
    "side1": (2, 0),     # 측면 걷기 A
    "side2": (2, 1),     # 측면 걷기 B
}


def main() -> None:
    os.makedirs(DEST_DIR, exist_ok=True)

    # 이전에 AI로 만든 스프라이트는 더 이상 안 쓰므로 정리
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

    # 바닥 타일과 가구도 가져와서 오피스 배경을 직접 조립할 수 있게 한다
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

    # 가구는 이름별 디렉토리 안에 PNG가 들어있다(DESK/DESK_FRONT.png 등).
    # PC는 켜진 상태가 3프레임이라 모니터 깜빡임 애니메이션에 쓸 수 있다.
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
