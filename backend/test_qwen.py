import asyncio
import base64
import httpx
from config import QWEN_API_KEY, QWEN_API_URL, QWEN_MODEL

async def test():
    with open("test_portrait.png", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": "Are you working?"}
                ]
            }
        ],
        "response_format": {"type": "json_object"}
    }
    
    print("Sending payload to", QWEN_API_URL)
    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.post(QWEN_API_URL, json=payload, headers=headers)
        print("Status code:", resp.status_code)
        print("Response:", resp.text)

if __name__ == "__main__":
    asyncio.run(test())
