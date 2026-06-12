"""End-to-end test: generate image → call API → verify result."""
import asyncio
import json
import httpx
from PIL import Image, ImageDraw, ImageFilter
import random

def create_test_image():
    """Generate a portrait-like test image."""
    w, h = 512, 640
    img = Image.new("RGB", (w, h), (30, 30, 40))

    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(h):
        r = int(30 + (y / h) * 20)
        g = int(30 + (y / h) * 15)
        b = int(40 + (y / h) * 30)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Face oval
    cx, cy = w // 2, h // 2 - 40
    rx, ry = 120, 150
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(220, 185, 150))

    # Eyes
    eye_y = cy - 30
    draw.ellipse([cx - 50, eye_y - 15, cx - 20, eye_y + 15], fill=(255, 255, 255))
    draw.ellipse([cx + 20, eye_y - 15, cx + 50, eye_y + 15], fill=(255, 255, 255))
    draw.ellipse([cx - 38, eye_y - 5, cx - 32, eye_y + 8], fill=(40, 30, 20))
    draw.ellipse([cx + 32, eye_y - 5, cx + 38, eye_y + 8], fill=(40, 30, 20))

    # Nose
    draw.line([(cx, cy - 10), (cx - 5, cy + 20), (cx + 5, cy + 20)], fill=(180, 150, 120), width=3)

    # Mouth
    mouth_y = cy + 50
    draw.arc([cx - 30, mouth_y - 10, cx + 30, mouth_y + 15], start=0, end=180, fill=(180, 120, 100), width=4)

    # Hair
    for i in range(2000):
        x = random.randint(cx - 150, cx + 150)
        y = random.randint(50, cy - 20)
        dist = ((x - cx) / 120) ** 2 + ((y - cy + 80) / 140) ** 2
        if dist < 1.2 and not (abs(x - cx) < 105 and abs(y - cy) < 130):
            draw.point((x, y), fill=(60, 40, 30))

    # Add some blur for realism
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    path = "test_portrait.png"
    img.save(path)
    return path

async def run_e2e():
    print("Creating test portrait...")
    img_path = create_test_image()
    print(f"Created: {img_path}")

    print("\nCalling API...")
    t0 = __import__("time").time()

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "http://127.0.0.1:8000/api/analyze",
            files={"file": ("portrait.png", img_bytes, "image/png")},
        )

    elapsed = __import__("time").time() - t0
    print(f"Response: {r.status_code} ({elapsed:.1f}s)")

    if r.status_code == 200:
        data = r.json()
        print(f"\nAnalysis ID: {data['analysis_id']}")
        print(f"\nScores:")
        for k, v in data["scores"].items():
            bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
            print(f"  {k:25s}: {v*100:5.1f}% {bar}")
        print(f"\nAI Personality: {data['report']['ai_personality']}")
        print(f"Summary: {data['report']['summary'][:100]}...")
        print(f"\nVerdict:")
        print(f"  {data['report']['verdict']}")
        print(f"\nHeatmap: {len(data['heatmap'])} bytes (base64)")
        print("\n✅ E2E TEST PASSED")
        return True
    else:
        print(f"Error: {r.status_code}")
        print(r.text[:500])
        print("\n❌ E2E TEST FAILED")
        return False

if __name__ == "__main__":
    asyncio.run(run_e2e())
