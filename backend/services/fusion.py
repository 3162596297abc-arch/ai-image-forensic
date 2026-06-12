"""Truth Engine Production Fusion — Confidence Weighted & Arbitration Engine."""
from services.logger import AuditLogger
import config

def fuse_features(analysis_id: str, jury_results: list, hf_features: list) -> dict:
    """Fuse multi-modal evidence using confidence-weighted algorithm and conflict arbitration."""
    
    def get_evidence(name: str, default: float = 0.0) -> tuple:
        # Returns (signal_strength, confidence)
        for jr in jury_results:
            if isinstance(jr, list):
                for e in jr:
                    if e.get("signal_name") == name:
                        return e.get("signal_strength", default), e.get("confidence", 0.0)
        for e in hf_features:
            if e.get("signal_name") == name:
                return e.get("signal_strength", default), e.get("confidence", 0.0)
        return default, 0.0

    # 1. Generator Signature
    mj_sig, mj_conf = get_evidence("mj_signature")
    sd_sig, sd_conf = get_evidence("sd_signature")
    flux_sig, flux_conf = get_evidence("flux_signature")
    enh_sig, enh_conf = get_evidence("ai_enhancement_signature")
    
    gen_sigs = [(mj_sig, mj_conf), (sd_sig, sd_conf), (flux_sig, flux_conf), (enh_sig, enh_conf)]
    generator_signature, gen_conf = max(gen_sigs, key=lambda x: x[0])

    # 2. Structural Collapse
    fft_anomaly, fft_conf = get_evidence("fft_abnormal_spikes")
    edge_collapse, edge_conf = get_evidence("edge_collapse")
    local_repetition, rep_conf = get_evidence("local_repetition")
    
    structs = [(fft_anomaly, fft_conf), (edge_collapse, edge_conf), (local_repetition, rep_conf)]
    structural_collapse, struct_conf = max(structs, key=lambda x: x[0])

    # 3. Sensor Reality Missing
    cmos_absence, cmos_conf = get_evidence("cmos_noise_absence")
    randomness_absence, rand_conf = get_evidence("sensor_randomness_absence")
    lens_blur_anomaly, lens_conf = get_evidence("lens_blur_anomaly")
    
    sensors = [(cmos_absence, cmos_conf), (randomness_absence, rand_conf), (lens_blur_anomaly, lens_conf)]
    sensor_fake_score, sensor_conf = max(sensors, key=lambda x: x[0])

    # 4. ELA Auxiliary
    ela_anomaly, ela_conf = get_evidence("ela_anomaly")
    over_sharpening, sharp_conf = get_evidence("over_sharpening")

    # --- Confidence Weighted Formula ---
    # Score = Sum(Risk * Conf * Weight) / Sum(Conf * Weight)
    weights = [
        (generator_signature, gen_conf, config.WEIGHT_GENERATOR_SIG),
        (structural_collapse, struct_conf, config.WEIGHT_STRUCTURAL_COLLAPSE),
        (sensor_fake_score, sensor_conf, config.WEIGHT_SENSOR_REALITY)
    ]
    
    numerator = sum(risk * conf * w for risk, conf, w in weights)
    denominator = sum(conf * w for _, conf, w in weights)
    
    if denominator > 0:
        base_ai_risk = numerator / denominator
        system_degraded = False
    else:
        # Total failure of all modules, default to 0
        base_ai_risk = 0.0
        system_degraded = True

    AuditLogger.log_trace(analysis_id, "FusionCalculation", {
        "generator": {"score": generator_signature, "conf": gen_conf, "weight": config.WEIGHT_GENERATOR_SIG},
        "structural": {"score": structural_collapse, "conf": struct_conf, "weight": config.WEIGHT_STRUCTURAL_COLLAPSE},
        "sensor": {"score": sensor_fake_score, "conf": sensor_conf, "weight": config.WEIGHT_SENSOR_REALITY},
        "base_ai_risk": base_ai_risk
    })

    # --- Conflict Arbitration (Disabled per user request) ---
    scores = [generator_signature, structural_collapse, sensor_fake_score]
    max_score = max(scores)
    min_score = min(scores)
    
    conflict_detected = False
    conflict_msg = ""

    # --- Missing Module / Degradation Detection ---
    degraded_modules = []
    for jr in jury_results:
        if isinstance(jr, dict) and "features" in jr and "error" in jr["features"]:
            degraded_modules.append(jr.get("module", "Unknown Module"))
    
    # Also check if Qwen failed
    if gen_conf == 0.0:
        degraded_modules.append("Source Signature Sensor (Qwen)")

    # --- ELA Additive Penalty ---
    final_ai_risk = base_ai_risk
    ela_triggered = False
    
    if ela_anomaly > config.ELA_TAMPERING_THRESHOLD:
        ela_triggered = True
        # Instead of absolute floor, we add a penalty
        final_ai_risk += config.ELA_PENALTY_WEIGHT
        AuditLogger.log_trace(analysis_id, "ELAPenalty", {"ela_score": ela_anomaly, "action": f"Added penalty of {config.ELA_PENALTY_WEIGHT}"}, level="WARN")

    # Cap probability
    final_ai_risk = min(1.0, max(0.0, final_ai_risk))

    # Compile the final data dict
    v3_data = {
        "generator_signature": round(generator_signature, 3),
        "structural_collapse": round(structural_collapse, 3),
        "sensor_fake_score": round(sensor_fake_score, 3),
        "auxiliary_flags": {
            "ela_anomaly": round(ela_anomaly, 3),
            "over_sharpening": round(over_sharpening, 3)
        },
        "vlm_signatures": {
            "flux_signature": round(flux_sig, 3),
            "midjourney_signature": round(mj_sig, 3),
            "stable_diffusion_signature": round(sd_sig, 3)
        },
        "conflict_detected": conflict_detected,
        "conflict_msg": conflict_msg,
        "ela_triggered": ela_triggered,
        "system_degraded": system_degraded
    }

    # Generate triggers for the JSON report
    relation_triggers = []
    if conflict_detected:
        relation_triggers.append(conflict_msg)
    if ela_triggered:
        relation_triggers.append(f"【修图警报】ELA发现局部修图/拼接痕迹 (强度: {ela_anomaly:.2f})，已作为辅助证据扣分。")
    if system_degraded:
        relation_triggers.append(f"【系统故障】所有探测器传感器失效或被熔断，无法计算AI置信度，当前风险值仅作兜底参考。")
    if generator_signature > 0.6:
        relation_triggers.append(f"检测到强烈的AI模型特征指纹 (强度: {generator_signature:.2f})。")
    if structural_collapse > 0.5:
        relation_triggers.append("检测到局部空间结构崩塌（如边缘强制融合）。")
    if sensor_fake_score > 0.6:
        relation_triggers.append("检测不到真实CMOS传感器的物理底噪。")

    for mod in degraded_modules:
        relation_triggers.append(f"⚠️ 警告：[{mod}] 探测器当前负载过高或已熔断，被系统自动跳过。本次报告仅基于剩余模块数据推演。")

    v3_data["relation_triggers"] = relation_triggers

    # Determine Tier
    if final_ai_risk > 0.8:
        tier = "Critical"
    elif final_ai_risk > 0.5:
        tier = "High"
    elif final_ai_risk > 0.2:
        tier = "Moderate"
    else:
        tier = "Low"

    return {
        "ai_participation": round(final_ai_risk, 4),
        "tier": tier,
        "v3_system_data": v3_data
    }
