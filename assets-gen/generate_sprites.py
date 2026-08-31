"""Generates high-quality pixel-art sprites for the office scene.

Pipeline: generate at 512px with the SD1.5 pixel-art model -> downsample to 128px
+ color quantization to sharpen the pixel grid -> flood-fill the background
transparent -> save upscaled back to 512px with nearest-neighbor.

SDXL is unusable on this Mac (M5/MPS) since it takes 3-4 hours per image (measured).
512px/50 steps is the practical quality ceiling, at roughly 47 seconds per image.

Each character gets two poses, idle (standing) and walk (walking), so alternating
frames in the app makes them look like they're walking. Using the same seed keeps
the character's appearance consistent across both poses.
"""

from collections import deque

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

MODEL_ID = "kohbanye/pixel-art-style"
STYLE = ", detailed pixel art, crisp clean pixels, vibrant colors, plain solid white background, full body visible, centered"
NEG = "blurry, photorealistic, 3d render, text, watermark, low quality, jpeg artifacts, deformed, cropped, multiple people"

CHARACTERS = {
    "fundamentals": "financial analyst wearing glasses and a business suit, holding a clipboard",
    "news": "news reporter holding a newspaper, wearing a casual blazer",
    "technical": "tech analyst wearing a headset and a hoodie",
    "flow": "institutional trader in a business suit, holding a tablet",
    "bull": "confident optimistic trader in a suit with a green tie, thumbs up",
    "bear": "cautious pessimistic trader in a suit with a dark red tie, arms crossed",
    "trader": "decisive stock trader wearing a headset, sharp business suit",
    "risk": "strict risk manager in a dark suit, holding a folder",
}

POSES = {
    "idle": "standing still, facing viewer, relaxed pose",
    "walk": "walking, mid-stride, one leg forward, side view, arms swinging",
}

BACKGROUND_PROMPT = (
    "pixel art wide office interior, rows of desks with computer monitors, "
    "large windows with bright warm sunlight streaming in, plants, modern trading floor, "
    "detailed pixel art background, no people"
)


def refine_pixel_art(img: Image.Image, grid: int = 128, colors: int = 48) -> Image.Image:
    """Downsamples and color-quantizes the image to sharpen the pixel grid."""
    small = img.resize((grid, grid), Image.LANCZOS)
    small = small.quantize(colors=colors, method=Image.MAXCOVERAGE).convert("RGB")
    return small


def make_background_transparent(img: Image.Image) -> Image.Image:
    """Flood-fills from the four corners to make only the background transparent.
    White areas inside the character (e.g. a shirt) aren't connected to the
    corners, so they're left untouched."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()

    def is_bg(p):
        r, g, b, _ = p
        return r > 200 and g > 200 and b > 200

    visited = [[False] * w for _ in range(h)]
    q = deque()
    for cx, cy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if is_bg(px[cx, cy]):
            q.append((cx, cy))
            visited[cy][cx] = True

    while q:
        x, y = q.popleft()
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and is_bg(px[nx, ny]):
                visited[ny][nx] = True
                q.append((nx, ny))
    return img


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device: {device}", flush=True)
    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, safety_checker=None
    ).to(device)
    print("모델 로드 완료", flush=True)

    total = len(CHARACTERS) * len(POSES) + 1
    done = 0

    for key, desc in CHARACTERS.items():
        # Fix the seed per character so it looks like the same person across poses
        seed = abs(hash(key)) % (2**31)
        for pose_name, pose_desc in POSES.items():
            gen = torch.Generator(device="cpu").manual_seed(seed)
            image = pipe(
                f"pixel art, full body character sprite, {desc}, {pose_desc}{STYLE}",
                negative_prompt=NEG,
                num_inference_steps=50,
                guidance_scale=8.0,
                width=512,
                height=512,
                generator=gen,
            ).images[0]

            refined = refine_pixel_art(image)
            transparent = make_background_transparent(refined)
            out = transparent.resize((512, 512), Image.NEAREST)
            out.save(f"sprite_{key}_{pose_name}.png")

            done += 1
            print(f"[{done}/{total}] sprite_{key}_{pose_name}.png 완료", flush=True)

    print("배경 생성 중...", flush=True)
    bg = pipe(
        BACKGROUND_PROMPT,
        negative_prompt=NEG,
        num_inference_steps=50,
        guidance_scale=8.0,
        width=768,
        height=448,
    ).images[0]
    # Background: pixel refinement only, no transparency (keep aspect ratio)
    bg_small = bg.resize((192, 112), Image.LANCZOS)
    bg_small = bg_small.quantize(colors=64, method=Image.MAXCOVERAGE).convert("RGB")
    bg_small.resize((768, 448), Image.NEAREST).save("sprite_office_background.png")
    print(f"[{total}/{total}] 전체 완료", flush=True)


if __name__ == "__main__":
    main()
