import json
import time
import urllib.request
from PIL import Image, ImageDraw, ImageFilter
import random

# Create test portrait
w, h = 512, 640
img = Image.new("RGB", (w, h), (30, 30, 40))
draw = ImageDraw.Draw(img)
for y in range(h):
    r = int(30 + (y / h) * 20)
    g = int(30 + (y / h) * 15)
    b = int(40 + (y / h) * 30)
    draw.line([(0, y), (w, y)], fill=(r, g, b))

cx, cy = w // 2, h // 2 - 40
draw.ellipse([cx - 120, cy - 150, cx + 120, cy + 150], fill=(220, 185, 150))
eye_y = cy - 30
draw.ellipse([cx - 50, eye_y - 15, cx - 20, eye_y + 15], fill=(255, 255, 255))
draw.ellipse([cx + 20, eye_y - 15, cx + 50, eye_y + 15], fill=(255, 255, 255))
draw.ellipse([cx - 38, eye_y - 5, cx - 32, eye_y + 8], fill=(40, 30, 20))
draw.ellipse([cx + 32, eye_y - 5, cx + 38, eye_y + 8], fill=(40, 30, 20))
img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

import io
buf = io.BytesIO()
img.save(buf, format="PNG")
img_bytes = buf.getvalue()
print(f"Image: {len(img_bytes)} bytes")

# Multipart form-data
boundary = b"----PythonTestBoundary12345"
body = b""
body += b"--" + boundary + b"\r\n"
body += b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
body += b"Content-Type: image/png\r\n"
body += b"\r\n"
body += img_bytes
body += b"\r\n"
body += b"--" + boundary + b"--\r\n"

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/analyze",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=" + boundary.decode()},
    method="POST",
)

t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        elapsed = time.time() - t0
        data = json.loads(resp.read())
        print(f"Status: {resp.status} ({elapsed:.1f}s)")
        print(f"ID: {data['analysis_id']}")
        print(f"AI Participation: {data['scores']['ai_participation']*100:.1f}%")
        print(f"Personality: {data['report']['ai_personality']}")
        print(f"Verdict: {data['report']['verdict'][:80]}...")
        print("PASS")
except Exception as e:
    elapsed = time.time() - t0
    print(f"Error ({elapsed:.1f}s): {e}")
