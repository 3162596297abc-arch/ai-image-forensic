import json, time, urllib.request

with open("demo_test.png", "rb") as f:
    img = f.read()
print(f"Image: {len(img)} bytes")

boundary = b"----TestBoundary999"
body = (b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
        b"Content-Type: image/png\r\n\r\n"
        + img +
        b"\r\n--" + boundary + b"--\r\n")

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/analyze",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=" + boundary.decode()},
    method="POST",
)

t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        print(f"OK ({time.time()-t0:.1f}s)")
        print(f"ID: {data['analysis_id']}")
        print(f"AI Participation: {data['scores']['ai_participation']*100:.0f}%")
        print(f"Personality: {data['report']['ai_personality']}")
except Exception as e:
    print(f"FAIL ({time.time()-t0:.1f}s): {e}")
