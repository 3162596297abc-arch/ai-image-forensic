"""Qwen-VL Source Signature Sensor for Truth Engine Lite."""
import json
import base64
import random
import asyncio
import httpx
import traceback
from services.logger import AuditLogger
from config import HUGGINGFACE_API_TOKEN, HUGGINGFACE_API_URL

async def analyze_image(image_bytes: bytes, api_url: str = "", api_key: str = "", model_name: str = "qwen-vl-max", analysis_id: str = "unknown") -> list:
    """Run AI image detection purely as a Source Signature Sensor."""
    
    # We will try Qwen first, then fallback to HF
    qwen_failed = False
    
    if not api_key:
        AuditLogger.log_trace(analysis_id, "SourceSignature", {"status": "bypassed", "reason": "No Qwen API key"}, level="WARN")
        qwen_failed = True

    try:
        img_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        prompt = """你是一个专业的图像法医分析系统（Forensic Source Sensor）。
请仔细观察这张图片，专门寻找当前主流AI生成模型（如Midjourney, Stable Diffusion, Flux等）留下的独有视觉签名。
不要判断图片“看起来是否真实”，只根据微观纹理、塑料光感、特定噪点分布，指出它带有哪种生成器的痕迹。

你必须严格输出如下格式的JSON，不要包含任何其他文字或Markdown标记：
{
  "flux_signature": 0.81, // 0.0到1.0，属于Flux特征的概率
  "midjourney_signature": 0.22, // 属于Midjourney特征的概率
  "sd_signature": 0.14, // 属于Stable Diffusion特征的概率
  "ai_enhancement_signature": 0.05 // 真实照片但被AI放大/重绘的概率
}
"""

        if not qwen_failed:
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                "response_format": {"type": "json_object"}
            }

            # Attempt 1 time only to avoid massive UI delays if network is dead
            for attempt in range(1):
                try:
                    # 12s timeout for cold starts, bypass broken system proxy with trust_env=False
                    async with httpx.AsyncClient(timeout=12.0, trust_env=False) as client:
                        resp = await client.post(api_url, json=payload, headers=headers)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data["choices"][0]["message"]["content"]
                            content = content.replace("```json", "").replace("```", "").strip()
                            result = json.loads(content)
                            
                            AuditLogger.log_trace(analysis_id, "SourceSignature", {"status": "success", "signatures": result})
                            return _build_scores(result, confidence_override=0.85)
                        else:
                            AuditLogger.log_error(analysis_id, "SourceSignatureAPI", f"Attempt {attempt+1} Status {resp.status_code}: {resp.text}")
                except httpx.TimeoutException:
                    AuditLogger.log_error(analysis_id, "SourceSignatureTimeout", f"Attempt {attempt+1} timed out after 12.0s")
                except Exception as e:
                    AuditLogger.log_error(analysis_id, "SourceSignatureNetworkError", f"Attempt {attempt+1} error: {e}\n{traceback.format_exc()}")
            
            qwen_failed = True

        # FALLBACK: HuggingFace API (AIorNot or similar ViT model)
        if qwen_failed and HUGGINGFACE_API_TOKEN:
            AuditLogger.log_trace(analysis_id, "SourceSignatureFallback", {"status": "falling back to HF"}, level="WARN")
            hf_headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
            try:
                async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                    resp = await client.post(HUGGINGFACE_API_URL, content=image_bytes, headers=hf_headers)
                    if resp.status_code == 200:
                        results = resp.json()
                        # Usually returns [{"label": "fake", "score": 0.9}, {"label": "real", "score": 0.1}]
                        fake_score = 0.0
                        for r in results:
                            if isinstance(r, dict) and r.get("label", "").lower() == "fake":
                                fake_score = r.get("score", 0.0)
                        
                        AuditLogger.log_trace(analysis_id, "SourceSignatureHF", {"status": "success", "fake_score": fake_score})
                        
                        # Translate generic fake score into our signature format
                        return _build_scores({
                            "flux_signature": fake_score,
                            "midjourney_signature": fake_score,
                            "sd_signature": fake_score,
                            "ai_enhancement_signature": fake_score * 0.5
                        }, confidence_override=0.60) # Lower confidence for fallback
            except Exception as e:
                AuditLogger.log_error(analysis_id, "SourceSignatureHFError", f"HF Fallback error: {e}")

    except Exception as e:
        AuditLogger.log_error(analysis_id, "SourceSignatureException", str(e), traceback.format_exc())

    # Graceful degradation fallback if all APIs fail
    AuditLogger.log_trace(analysis_id, "SourceSignatureDegraded", {"status": "degraded", "action": "confidence_zero"}, level="WARN")
    return _build_scores({"flux_signature": 0, "midjourney_signature": 0, "sd_signature": 0}, confidence_override=0.0)

def _mock_analysis() -> list:
    r = random.Random()
    return _build_scores({
        "flux_signature": r.uniform(0.1, 0.4),
        "midjourney_signature": r.uniform(0.1, 0.4),
        "sd_signature": r.uniform(0.1, 0.4),
        "ai_enhancement_signature": r.uniform(0.01, 0.1)
    })

def _build_scores(signatures: dict, confidence_override: float = None) -> list:
    flux = max(0.0, min(1.0, signatures.get("flux_signature", 0.0)))
    mj = max(0.0, min(1.0, signatures.get("midjourney_signature", 0.0)))
    sd = max(0.0, min(1.0, signatures.get("sd_signature", 0.0)))
    enh = max(0.0, min(1.0, signatures.get("ai_enhancement_signature", 0.0)))

    def get_conf(default: float):
        return default if confidence_override is None else confidence_override

    return [
        {
            "signal_name": "mj_signature",
            "signal_strength": round(mj, 3),
            "signal_type": "generative",
            "confidence": get_conf(0.85),
            "source": "sgs"
        },
        {
            "signal_name": "sd_signature",
            "signal_strength": round(sd, 3),
            "signal_type": "generative",
            "confidence": get_conf(0.85),
            "source": "sgs"
        },
        {
            "signal_name": "flux_signature",
            "signal_strength": round(flux, 3),
            "signal_type": "generative",
            "confidence": get_conf(0.80),
            "source": "sgs"
        },
        {
            "signal_name": "ai_enhancement_signature",
            "signal_strength": round(enh, 3),
            "signal_type": "generative",
            "confidence": get_conf(0.70),
            "source": "sgs"
        }
    ]
