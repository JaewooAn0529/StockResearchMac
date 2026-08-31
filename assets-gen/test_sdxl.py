import time

import torch
from diffusers import StableDiffusionXLPipeline

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"device: {device}")

t0 = time.time()
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float32
).to(device)
pipe.load_lora_weights("nerijs/pixel-art-xl")
print(f"모델+LoRA 로드: {time.time() - t0:.1f}초")

t0 = time.time()
image = pipe(
    "pixel art, a detailed character portrait bust shot, financial analyst wearing glasses and a suit, "
    "holding a clipboard with charts, serious expression, high quality pixel art, detailed shading, plain solid white background",
    negative_prompt="blurry, photorealistic, 3d render, text, watermark",
    num_inference_steps=50,
    guidance_scale=7.5,
    width=1024,
    height=1024,
).images[0]
print(f"1장 생성: {time.time() - t0:.1f}초")
image.save("test_sdxl_output.png")
print("저장됨: test_sdxl_output.png")
