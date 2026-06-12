import urllib.request, urllib.error
import json

url = "http://127.0.0.1:8001/api/analyze"
with open("demo_test.png", "rb") as f:
    image_data = f.read()

import io
boundary = "----FormBoundary7MA4YWxkTrZu0gW"
body = io.BytesIO()
body.write(f"--{boundary}\r\n".encode())
body.write(b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n')
body.write(b"Content-Type: image/png\r\n\r\n")
body.write(image_data)
body.write(f"\r\n--{boundary}--\r\n".encode())

req = urllib.request.Request(url, data=body.getvalue(),
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST")

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        print(f"Status: {resp.status}")
        print(f"AI: {data['jury']['ai_participation']}")
        print("PASS")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} — {e.read().decode()[:500]}")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
