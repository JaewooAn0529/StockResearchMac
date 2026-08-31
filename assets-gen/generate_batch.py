"""토론 화면용 픽셀아트 에셋 일괄 생성. 모델을 한 번만 로드해서 여러 장 뽑는다."""

import torch
from diffusers import StableDiffusionPipeline

MODEL_ID = "kohbanye/pixel-art-style"
STYLE_SUFFIX = ", plain solid white background, centered, simple flat colors, clean pixel art"

CHARACTERS = {
    "fundamentals": "pixel art character portrait bust shot, financial analyst wearing glasses and a suit, holding a clipboard with charts, serious expression",
    "news": "pixel art character portrait bust shot, news reporter analyst holding a newspaper, casual blazer, curious expression",
    "technical": "pixel art character portrait bust shot, tech analyst wearing a headset, hoodie, looking at data, focused expression",
    "flow": "pixel art character portrait bust shot, institutional trading analyst in a suit, holding arrows and flow chart icons, calm expression",
    "bull": "pixel art character portrait bust shot, optimistic stock market bull researcher, green tie, confident smiling expression, thumbs up",
    "bear": "pixel art character portrait bust shot, cautious stock market bear researcher, dark red tie, arms crossed, skeptical expression",
    "trader": "pixel art character portrait bust shot, decisive stock trader wearing a headset in front of multiple monitors, sharp focused expression",
    "risk": "pixel art character portrait bust shot, strict risk manager holding a shield icon and a clipboard, stern serious expression",
}

BACKGROUND_PROMPT = (
    "pixel art wide office room interior, 8 empty desks with computer monitors arranged in two rows, "
    "modern trading floor office, big windows, clean simple retro game background, no people"
)


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device: {device}")
    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, safety_checker=None
    ).to(device)
    print("모델 로드 완료")

    for key, prompt in CHARACTERS.items():
        print(f"생성 중: {key}")
        image = pipe(
            prompt + STYLE_SUFFIX,
            negative_prompt="blurry, photorealistic, 3d render, text, watermark, multiple people, full body",
            num_inference_steps=30,
            guidance_scale=7.5,
        ).images[0]
        image.save(f"char_{key}.png")

    print("생성 중: background")
    bg = pipe(
        BACKGROUND_PROMPT,
        negative_prompt="blurry, photorealistic, 3d render, text, watermark, people, characters",
        num_inference_steps=30,
        guidance_scale=7.5,
        width=768,
        height=448,
    ).images[0]
    bg.save("office_background.png")

    print("전체 완료")


if __name__ == "__main__":
    main()
