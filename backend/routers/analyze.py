import uuid
import time
import asyncio
from collections import defaultdict
from io import BytesIO

import gc
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, BackgroundTasks
from PIL import Image

import config
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
# 1. Concurrency Lock: Max 2 simultaneous OpenCV matrix calculations for 512MB RAM
ANALYSIS_SEMAPHORE = asyncio.Semaphore(2)

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
    
    # 内存泄漏防护：列表为空则删除该 IP 键（避免字典随陌生 IP 无限增长）
    if not RATE_LIMIT_STORE[client_ip]:
        del RATE_LIMIT_STORE[client_ip]
        # 不能在此 return：必须继续向下记录本次时间戳，否则首个请求永不入账、限流彻底失效
    
    if len(RATE_LIMIT_STORE[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        AuditLogger.log_trace("SYSTEM", "RateLimitExceeded", {"ip": client_ip})
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试 (Too Many Requests)")
        
    RATE_LIMIT_STORE[client_ip].append(now)


@router.post("/analyze")
async def analyze(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload an image and receive multi-module forensic analysis."""
    _check_rate_limit(request)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "请上传图片文件")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "图片大小不能超过10MB")

    try:
        img = Image.open(BytesIO(contents))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # --- 预处理解耦（v4）：产出两份输入 ---
        # raw_bytes：原生信号视图（保留 CMOS 底噪 / JPEG 压缩历史 / EXIF），
        #   供 CMOS、ELA、栅格周期、局部篡改、元数据等模块使用。
        #   大图取原生中心裁块（只裁不缩放，内存受限）；小图直接用原始字节（连 EXIF 一起保住）。
        W, H = img.size
        if max(W, H) > config.RAW_MAX_SIDE:
            s = config.RAW_MAX_SIDE
            left = max(0, (W - s) // 2)
            top = max(0, (H - s) // 2)
            raw_crop = img.crop((left, top, min(W, left + s), min(H, top + s)))
            rb = BytesIO()
            raw_crop.save(rb, format="PNG")
            raw_bytes = rb.getvalue()
        else:
            raw_bytes = contents

        # contents（proc）：降采样视图，抗压缩/缩放伪影，供 FFT/边缘等模块使用。
        # 用无损 PNG + 平滑插值，防止高频振铃/JPEG 伪影被 FFT 误判。
        img.thumbnail((config.PROC_MAX_SIDE, config.PROC_MAX_SIDE), Image.Resampling.BILINEAR)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        contents = buffer.getvalue()
    except Exception:
        raise HTTPException(400, "无法解析该图片文件")

    analysis_id = str(uuid.uuid4())
    AuditLogger.log_trace(analysis_id, "APIRequestStart", {"file_size": len(contents)})

    # Apply global concurrency lock to prevent OOM / CPU maxing during local OpenCV operations
    async def _run_jury_with_lock():
        try:
            async with asyncio.timeout(80.0): # 80s wait for slow free tier CPUs
                async with ANALYSIS_SEMAPHORE:
                    return await run_jury(analysis_id, contents, raw_bytes)
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

    # Clear memory aggressively for 512MB limit
    background_tasks.add_task(gc.collect)

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
