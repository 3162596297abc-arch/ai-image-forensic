"""Direct backend test without network."""
import asyncio
import sys
sys.path.insert(0, ".")

from services.ai_detector import analyze_image
from services.heatmap import generate_heatmap
from services.deepseek_report import generate_report
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

async def test():
    with open("test_img.png", "rb") as f:
        img_bytes = f.read()

    # Test AI detection
    scores = await analyze_image(img_bytes, "", "")
    print(f"AI detection OK: participation={scores['ai_participation']}")
    print(f"  Scores: { {k: round(v,2) for k,v in scores.items()} }")

    # Test heatmap
    heatmap = generate_heatmap(img_bytes, scores["ai_participation"])
    print(f"Heatmap OK: {len(heatmap)} chars")

    # Test DeepSeek report
    print(f"DeepSeek key: {'SET' if DEEPSEEK_API_KEY else 'EMPTY'}")
    report = await generate_report(scores, DEEPSEEK_API_KEY, DEEPSEEK_API_URL)
    print(f"Report OK: personality={report['ai_personality']}")

asyncio.run(test())
