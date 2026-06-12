"""Test the full API flow end-to-end."""
import httpx
import time

print("Starting test...")
with open("demo_test.png", "rb") as f:
    image_data = f.read()

print(f"Image size: {len(image_data)} bytes")
print("Connecting to http://127.0.0.1:8001/api/analyze ...")

try:
    resp = httpx.post(
        "http://127.0.0.1:8001/api/analyze",
        files={"file": ("test.png", image_data, "image/png")},
        timeout=120.0,
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Analysis ID: {data['analysis_id']}")
        print(f"AI Participation: {data['jury']['ai_participation']}")
        print(f"Tier: {data['jury']['tier']}")
        print(f"HF Detection: {data['hf_detection']}")
        print(f"Total modules: {len(data['module_results'])}")
        print("PASS")
    else:
        print(f"Error body: {resp.text[:500]}")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
