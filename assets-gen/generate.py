"""로컬 Stable Diffusion으로 픽셀아트 캐릭터/배경을 생성한다.
Apple Silicon MPS 가속 사용. 무료, 크레딧 불필요 — Ollama와 같은 패턴.
"""

import sys

import torch
from diffusers import StableDiffusionPipeline

MODEL_CANDIDATES = [
    "kohbanye/pixel-art-style",  # SD1.5 픽셀아트 파인튜닝 (있으면 이걸 우선 사용)
    "sd-legacy/stable-diffusion-v1-5",  # 폴백: 범용 모델 + 프롬프트로 픽셀아트 유도
]


def load_pipeline():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device: {device}")
    last_err = None
    for model_id in MODEL_CANDIDATES:
        try:
            print(f"모델 로드 시도: {model_id}")
            pipe = StableDiffusionPipeline.from_pretrained(
                model_id, torch_dtype=torch.float32, safety_checker=None
            )
            pipe = pipe.to(device)
            print(f"성공: {model_id}")
            return pipe, model_id
        except Exception as e:
            print(f"실패 ({model_id}): {e}")
            last_err = e
    raise last_err


if __name__ == "__main__":
    prompt = sys.argv[1]
    out_path = sys.argv[2]
    pipe, used_model = load_pipeline()

    suffix = "" if "pixel-art" in used_model else ", pixel art style, 16-bit retro game sprite"
    full_prompt = prompt + suffix

    image = pipe(
        full_prompt,
        negative_prompt="blurry, photorealistic, 3d render, text, watermark",
        num_inference_steps=30,
        guidance_scale=7.5,
    ).images[0]
    image.save(out_path)
    print(f"저장됨: {out_path}")
