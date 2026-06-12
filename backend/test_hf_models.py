"""Test which HuggingFace AI detection models actually work."""
import httpx
import os
import time
from pathlib import Path
from dotenv import dotenv_values

root = Path(__file__).resolve().parent.parent
env = dotenv_values(str(root / ".env.local"))
key = env.get("HUGGINGFACE_API_KEY", "")

with open("demo_test.png", "rb") as f:
    data = f.read()

models = [
    "NYUAD-ComNets/NYUAD_AI-generated_images_detector",
    "Reju983/ai-generated-image-detector",
    "not-lain/real-or-ai",
    "prithivMLmods/Deepfake-Detection",
    "awsaf49/real-vs-ai-img-detector",
    "Organika/synthetic-image-detector",
]

for mid in models:
    url = f"https://api-inference.huggingface.co/models/{mid}"
    try:
        resp = httpx.post(
            url, content=data,
            headers={"Authorization": f"Bearer {key}"},
            timeout=45
        )
        status = "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"
        body = resp.text[:250]
    except Exception as e:
        status = "ERROR"
        body = str(e)[:100]
    print(f"[{status}] {mid}")
    print(f"  {body}")
    print()
    time.sleep(1)
