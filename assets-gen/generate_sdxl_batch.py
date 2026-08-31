"""SDXL + pixel-art-xl LoRA로 고품질 캐릭터를 뽑는다. 캐릭터마다 base 포즈를
txt2img로 만들고, 그 이미지를 img2img 시드로 삼아 걷는/제스처 포즈를 하나 더
뽑는다 — 완전히 새로 생성하면 프레임마다 캐릭터 생김새가 달라지는데, img2img로
base에서 파생시키면 같은 캐릭터처럼 유지된다.
"""

import torch
from diffusers import StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline

STYLE = ", pixel art, high quality detailed pixel art, detailed shading, plain solid white background, centered, clean"
NEG = "blurry, photorealistic, 3d render, text, watermark, multiple people, full body, low quality, simple"

CHARACTERS = {
    "fundamentals": "a character bust shot, financial analyst wearing glasses and a suit, holding a clipboard with charts, serious expression",
    "news": "a character bust shot, news reporter analyst holding a newspaper, casual blazer, curious expression",
    "technical": "a character bust shot, tech analyst wearing a headset, hoodie, looking at data, focused expression",
    "flow": "a character bust shot, institutional trading analyst in a suit, holding arrows and flow chart icons, calm expression",
    "bull": "a character bust shot, optimistic stock market bull researcher, green tie, confident smiling expression, thumbs up",
    "bear": "a character bust shot, cautious stock market bear researcher with a bear-like face, dark red tie, arms crossed, skeptical expression",
    "trader": "a character bust shot, decisive stock trader wearing a headset in front of multiple monitors, sharp focused expression",
    "risk": "a character bust shot, strict risk manager holding a shield icon and a clipboard, stern serious expression",
}

POSE_PROMPT_SUFFIX = ", waving one hand up in a gesture, slightly different pose, mid-action"

BACKGROUND_PROMPT = (
    "pixel art wide office room interior, 8 empty desks with computer monitors arranged in two rows, "
    "modern trading floor office, big windows with bright sunlight streaming in, warm sunny lighting, "
    "clean detailed retro game background, no people, high quality pixel art"
)


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device: {device}")

    base_pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float32
    ).to(device)
    base_pipe.load_lora_weights("nerijs/pixel-art-xl")
    print("SDXL + LoRA 로드 완료")

    img2img_pipe = StableDiffusionXLImg2ImgPipeline(**base_pipe.components).to(device)
    print("img2img 파이프라인 준비 완료")

    for key, prompt in CHARACTERS.items():
        print(f"[{key}] base 생성 중...")
        base_image = base_pipe(
            prompt + STYLE,
            negative_prompt=NEG,
            num_inference_steps=50,
            guidance_scale=7.5,
            width=1024,
            height=1024,
        ).images[0]
        base_image.save(f"hq_{key}_idle.png")

        print(f"[{key}] 포즈 프레임 생성 중...")
        pose_image = img2img_pipe(
            prompt + POSE_PROMPT_SUFFIX + STYLE,
            image=base_image,
            negative_prompt=NEG,
            strength=0.55,
            num_inference_steps=50,
            guidance_scale=7.5,
        ).images[0]
        pose_image.save(f"hq_{key}_pose.png")

    print("배경 생성 중...")
    bg = base_pipe(
        BACKGROUND_PROMPT,
        negative_prompt=NEG,
        num_inference_steps=50,
        guidance_scale=7.5,
        width=1536,
        height=896,
    ).images[0]
    bg.save("hq_office_background.png")

    print("전체 완료")


if __name__ == "__main__":
    main()
