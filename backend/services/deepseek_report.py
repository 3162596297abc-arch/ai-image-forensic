import json
import httpx
from services.logger import AuditLogger

SYSTEM_PROMPT = """你是一个帮普通人看懂图片检测结果的助手。想象你在跟一个完全不懂技术的朋友说话。

铁律：
1. 绝对禁止出现这些词及其同类：仲裁、熔断、偏差、阈值、置信度、覆盖、降级、探测器、传感器、模块、底噪、伪影、ELA、CMOS、FFT、风险值、威胁等级。
2. 禁止复述任何数字或百分比（界面已经展示了数字，你只负责解释含义）。
3. 不脑补输入里不存在的证据；客观陈述，不吓唬用户。
4. ai_probability_summary 最多两句话：直接回答"这张图更像真拍的还是 AI 做的，最关键的理由是什么"。

输出必须为严格的 JSON：
{
  "ai_probability_summary": "两句话以内的人话结论",
  "dimensions": {
    "sensor": { "description": "一两句话：光线、阴影、颗粒感像不像真相机拍的？", "suggestion": "给用户的一句话提示，没有就留空字符串" },
    "structural": { "description": "一两句话：物体边缘和结构有没有拼凑感？", "suggestion": "同上" },
    "spatial": { "description": "一两句话：有没有 AI 绘图软件的画风痕迹？", "suggestion": "同上" },
    "editing": { "description": "一两句话：有没有被P过、拼接过的痕迹？", "suggestion": "同上" }
  }
}
"""

# —— 仅用于把数值转成给 LLM 看的人话（文案层，不参与任何评分计算） ——
_TIER_PLAIN = {
    "Low": "基本可信，没发现明显问题",
    "Moderate": "有些可疑，存在一些异常",
    "High": "很可能有 AI 参与",
    "Critical": "几乎可以确定是 AI 生成或被篡改过",
}

def _qual(x: float) -> str:
    if x >= 0.7:
        return "很可疑"
    if x >= 0.4:
        return "有点可疑"
    return "正常"

async def generate_report(analysis_id: str, scores: dict, fusion_result: dict, api_key: str, api_url: str) -> dict:
    """Generate dual-layer report: strict machine evidence + LLM translation."""
    
    # Layer 1: Strict JSON Evidence (The absolute truth)
    machine_evidence = _build_machine_evidence(fusion_result)
    AuditLogger.log_trace(analysis_id, "Layer1Evidence", machine_evidence)
    
    # Layer 2: LLM Translation (Can be bypassed if no API key or failed)
    if not api_key:
        AuditLogger.log_trace(analysis_id, "LLMTranslation", {"status": "bypassed"}, level="WARN")
        return _merge_report(machine_evidence, _mock_llm_text(fusion_result))

    v3_data = fusion_result.get("v3_system_data", {})
    skipped = any("跳过" in t for t in v3_data.get("relation_triggers", []))

    user_prompt = f"""这张图片的检测情况如下（已经转成日常说法，请只基于这些信息输出 JSON，不要发明新证据）：

- 总体判断倾向：{_TIER_PLAIN.get(fusion_result['tier'], '有些可疑')}
- 光线阴影和颗粒感（像不像真相机拍的）：{_qual(v3_data.get('sensor_fake_score', 0.0))}
- 物体边缘和结构（有没有拼凑感）：{_qual(v3_data.get('structural_collapse', 0.0))}
- AI 绘图软件的画风痕迹：{_qual(v3_data.get('generator_signature', 0.0))}
- 修图/拼接痕迹：{'发现了明显痕迹' if v3_data.get('ela_triggered') else _qual(v3_data.get('auxiliary_flags', {}).get('ela_anomaly', 0.0))}
{'- 提醒：本次有部分检测项没能完成，结论是根据其余项得出的。' if skipped else ''}

请严格按 JSON 格式输出 ai_probability_summary 和 4 个维度的 description 与 suggestion。"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1, # Extremely low temperature to prevent hallucination
        "max_tokens": 1000,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        try:
            resp = await client.post(api_url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                llm_text = json.loads(content)
                AuditLogger.log_trace(analysis_id, "LLMTranslation", {"status": "success", "content": llm_text})
                return _merge_report(machine_evidence, llm_text)
            else:
                AuditLogger.log_error(analysis_id, "LLMAPIError", f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            AuditLogger.log_error(analysis_id, "LLMException", str(e))

    AuditLogger.log_trace(analysis_id, "LLMTranslation", {"status": "fallback"}, level="WARN")
    return _merge_report(machine_evidence, _mock_llm_text(fusion_result))

def _build_machine_evidence(fusion_result: dict) -> dict:
    """Builds the Layer 1 unalterable machine JSON report."""
    v3_data = fusion_result.get("v3_system_data", {})
    
    def get_score_status(score):
        if score > 0.6: return "ANOMALOUS"
        if score > 0.4: return "SUSPICIOUS"
        return "STABLE"

    evidence = {
        "dimensions": {}
    }
    
    # 1. Sensor Reality
    sensor_score = v3_data.get("sensor_fake_score", 0.0)
    evidence["dimensions"]["sensor"] = {
        "status": get_score_status(sensor_score),
        "score": sensor_score,
        "sub_metrics": [{"name": "相机真实光感与噪点分析", "value": sensor_score}]
    }

    # 2. Structural & Texture Combined
    struct_score = v3_data.get("structural_collapse", 0.0)
    evidence["dimensions"]["structural"] = {
        "status": get_score_status(struct_score),
        "score": struct_score,
        "sub_metrics": [
            {"name": "边缘不自然拼接痕迹", "value": struct_score},
            {"name": "AI算法处理残留物", "value": struct_score}
        ]
    }

    # 3. Spatial (Generator Sig)
    gen_score = v3_data.get("generator_signature", 0.0)
    evidence["dimensions"]["spatial"] = {
        "status": get_score_status(gen_score),
        "score": gen_score,
        "sub_metrics": [{"name": "主流AI软件画风特征", "value": gen_score}]
    }

    # 4. Editing (ELA Auxiliary)
    ela = v3_data.get("auxiliary_flags", {}).get("ela_anomaly", 0.0)
    evidence["dimensions"]["editing"] = {
        "status": get_score_status(ela),
        "score": ela,
        "sub_metrics": [{"name": "后期人为P图篡改痕迹", "value": ela}]
    }

    evidence["jury"] = {
        "ai_participation": fusion_result["ai_participation"],
        "tier": fusion_result["tier"]
    }
    
    return evidence

def _merge_report(machine_evidence: dict, llm_text: dict) -> dict:
    """Merge the LLM translations into the strict machine evidence JSON."""
    
    report = machine_evidence.copy()
    report["ai_probability_summary"] = llm_text.get("ai_probability_summary", "机器取证分析完成。")
    
    llm_dims = llm_text.get("dimensions", {})
    for dim_name, ev_dim in report["dimensions"].items():
        ev_dim["description"] = llm_dims.get(dim_name, {}).get("description", "该项检查已完成，未生成文字说明。")
        ev_dim["suggestion"] = llm_dims.get(dim_name, {}).get("suggestion", "")
        
    return report

def _mock_llm_text(fusion_result: dict) -> dict:
    v3_data = fusion_result.get("v3_system_data", {})
    summary = "检测完成，各项结果见下方指标。"
    if v3_data.get("ela_triggered"):
        summary = "图片里发现了局部修图或拼接的痕迹，最终判断已经把这一点考虑进去了。"

    return {
        "ai_probability_summary": summary,
        "dimensions": {
            "sensor": {"description": "该项检查未发现明显问题。", "suggestion": ""},
            "structural": {"description": "该项检查未发现明显问题。", "suggestion": ""},
            "spatial": {"description": "该项检查未发现明显问题。", "suggestion": ""},
            "editing": {"description": "该项检查未发现明显问题。", "suggestion": ""}
        }
    }
