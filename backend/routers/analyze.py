import uuid
import time
import asyncio
from collections import defaultdict
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from PIL import Image

from config import (
    MAX_IMAGE_SIZE,
    DEEPSEEK_API_KEY, DEEPSEEK_API_URL,
    QWEN_API_URL, QWEN_API_KEY, QWEN_MODEL,
)
from services.ai_detector import analyze_image
from services.jury import run_jury
from services.deepseek_report import generate_report
from services.fusion import fuse_features
from services.logger import AuditLogger

router = APIRouter(prefix="/api", tags=["analysis"])

# --- Phase 2: High Availability Protections ---
# 1. Concurrency Lock: Max 10 simultaneous OpenCV matrix calculations
ANALYSIS_SEMAPHORE = asyncio.Semaphore(10)

# 2. In-Memory Token Bucket Rate Limiter
# Format: { "ip_address": [timestamp1, timestamp2, ...] }
RATE_LIMIT_STORE = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 50
RATE_LIMIT_WINDOW_SEC = 60.0

def _check_rate_limit(request: Request):
    """Raise 429 if the client exceeds the rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean up old timestamps outside the window
    RATE_LIMIT_STORE[client_ip] = [ts for ts in RATE_LIMIT_STORE[client_ip] if now - ts < RATE_LIMIT_WINDOW_SEC]
    
    if len(RATE_LIMIT_STORE[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        AuditLogger.log_trace("SYSTEM", "RateLimitExceeded", {"ip": client_ip})
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试 (Too Many Requests)")
        
    RATE_LIMIT_STORE[client_ip].append(now)


@router.post("/analyze")
async def analyze(request: Request, file: UploadFile = File(...)):
    """Upload an image and receive multi-module forensic analysis."""
    _check_rate_limit(request)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "请上传图片文件")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "图片大小不能超过10MB")

    try:
        img = Image.open(BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(400, "无法解析该图片文件")

    analysis_id = str(uuid.uuid4())
    AuditLogger.log_trace(analysis_id, "APIRequestStart", {"file_size": len(contents)})

    # Apply global concurrency lock to prevent OOM / CPU maxing during local OpenCV operations
    async def _run_jury_with_lock():
        try:
            async with asyncio.timeout(10.0): # 10s queue wait timeout
                async with ANALYSIS_SEMAPHORE:
                    return await run_jury(analysis_id, contents)
        except TimeoutError:
            AuditLogger.log_error(analysis_id, "ConcurrencyQueueTimeout", "Too many concurrent requests, system rejected request.")
            raise HTTPException(503, "服务器当前负载过高，请稍后重试 (Service Unavailable)")

    # Run Qwen and local OpenCV Jury concurrently
    hf_result, jury_result = await asyncio.gather(
        analyze_image(contents, QWEN_API_URL, QWEN_API_KEY, QWEN_MODEL, analysis_id),
        _run_jury_with_lock()
    )

    # Step 3: Fuse OpenCV features + Qwen Signatures
    fusion_result = fuse_features(analysis_id, jury_result["module_results"], hf_result)

    # Reconstruct legacy scores dict
    scores = {
        "ai_probability": round(fusion_result["ai_participation"], 4),
        "human_probability": round(1.0 - fusion_result["ai_participation"], 4),
        "ai_participation": round(fusion_result["ai_participation"], 4),
    }

    # Step 4: Generate DeepSeek Report
    report = await generate_report(analysis_id, scores, fusion_result, DEEPSEEK_API_KEY, DEEPSEEK_API_URL)

    AuditLogger.log_trace(analysis_id, "APIRequestComplete", {"ai_participation": fusion_result["ai_participation"]})

    return {
        "analysis_id": analysis_id,
        "scores": scores,
        "heatmap": "", # Heatmap disabled
        "report": report,
        "hf_detection": {
            "model": QWEN_MODEL,
            "status": "success",
            "signatures": hf_result,
        },
        "jury": {
            "ai_participation": fusion_result["ai_participation"],
            "tier": fusion_result["tier"],
            "jury_phases": jury_result["jury_phases"],
        },
        "system_data": fusion_result.get("v3_system_data", {})
    }


@router.get("/health")
async def health():
    return {
        "status": "operational",
        "system": "Truth Engine Lite (Phase 1)",
        "modules": [
            "Source Signature Sensor (Qwen)",
            "Structural Collapse Detector (OpenCV)",
            "Sensor Reality Modeling (OpenCV)",
            "Retouch Detector (ELA)",
        ],
    }
