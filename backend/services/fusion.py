"""Truth Engine Fusion（v4）— 置信度加权 + 空间证据加性仲裁。

设计要点：
  - 全局加权平均处理"全图性"证据（生成器指纹 / 结构崩塌 / 传感器缺失）。
  - 局部篡改(local_tampering) 与 ELA 作为【加性证据】叠加——它们是"局部"信号，
    绝不能被全局平均稀释，否则"真底图+局部AI重绘"会被判为真（痛点3）。
  - grid_periodicity（栅格周期，痛点2）并入结构类，抗压缩失效仍能抓上采样栅格。
"""
from services.logger import AuditLogger
import config


def fuse_features(analysis_id: str, jury_results: list, hf_features: list) -> dict:
    def get_evidence(name: str, default: float = 0.0) -> tuple:
        for jr in jury_results:
            if isinstance(jr, list):
                for e in jr:
                    if e.get("signal_name") == name:
                        return e.get("signal_strength", default), e.get("confidence", 0.0)
        for e in hf_features:
            if e.get("signal_name") == name:
                return e.get("signal_strength", default), e.get("confidence", 0.0)
        return default, 0.0

    # 1. 生成器指纹（来自 Qwen VLM / HF）
    mj_sig, mj_conf = get_evidence("mj_signature")
    sd_sig, sd_conf = get_evidence("sd_signature")
    flux_sig, flux_conf = get_evidence("flux_signature")
    enh_sig, enh_conf = get_evidence("ai_enhancement_signature")
    gen_sigs = [(mj_sig, mj_conf), (sd_sig, sd_conf), (flux_sig, flux_conf), (enh_sig, enh_conf)]
    generator_signature, gen_conf = max(gen_sigs, key=lambda x: x[0])

    # 2. 结构崩塌（含新增 grid_periodicity 栅格周期）
    fft_anomaly, fft_conf = get_evidence("fft_abnormal_spikes")
    edge_collapse, edge_conf = get_evidence("edge_collapse")
    local_repetition, rep_conf = get_evidence("local_repetition")
    grid_periodicity, grid_conf = get_evidence("grid_periodicity")
    structs = [(fft_anomaly, fft_conf), (edge_collapse, edge_conf),
               (local_repetition, rep_conf), (grid_periodicity, grid_conf)]
    structural_collapse, struct_conf = max(structs, key=lambda x: x[0])

    # 3. 传感器真实性缺失
    cmos_absence, cmos_conf = get_evidence("cmos_noise_absence")
    randomness_absence, rand_conf = get_evidence("sensor_randomness_absence")
    lens_blur_anomaly, lens_conf = get_evidence("lens_blur_anomaly")
    sensors = [(cmos_absence, cmos_conf), (randomness_absence, rand_conf), (lens_blur_anomaly, lens_conf)]
    sensor_fake_score, sensor_conf = max(sensors, key=lambda x: x[0])

    # 4. 辅助/局部证据
    ela_anomaly, ela_conf = get_evidence("ela_anomaly")
    over_sharpening, sharp_conf = get_evidence("over_sharpening")
    local_tamper, lt_conf = get_evidence("local_tampering")
    anomaly_region_ratio, _ = get_evidence("anomaly_region_ratio")

    # --- 置信度加权（全局证据）---
    weights = [
        (generator_signature, gen_conf, config.WEIGHT_GENERATOR_SIG),
        (structural_collapse, struct_conf, config.WEIGHT_STRUCTURAL_COLLAPSE),
        (sensor_fake_score, sensor_conf, config.WEIGHT_SENSOR_REALITY),
    ]
    numerator = sum(risk * conf * w for risk, conf, w in weights)
    denominator = sum(conf * w for _, conf, w in weights)

    if denominator > 0:
        base_ai_risk = numerator / denominator
        system_degraded = False
    else:
        base_ai_risk = 0.0
        system_degraded = True

    AuditLogger.log_trace(analysis_id, "FusionCalculation", {
        "generator": {"score": generator_signature, "conf": gen_conf},
        "structural": {"score": structural_collapse, "conf": struct_conf},
        "sensor": {"score": sensor_fake_score, "conf": sensor_conf},
        "base_ai_risk": base_ai_risk,
    })

    scores = [generator_signature, structural_collapse, sensor_fake_score]
    conflict_detected = False
    conflict_msg = ""

    # --- 模块降级检测 ---
    degraded_modules = []
    for jr in jury_results:
        if isinstance(jr, dict) and "features" in jr and "error" in jr["features"]:
            degraded_modules.append(jr.get("module", "Unknown Module"))
    if gen_conf == 0.0:
        degraded_modules.append("Source Signature Sensor (Qwen)")

    final_ai_risk = base_ai_risk

    # --- ELA 加性扣分（弱辅助）---
    ela_triggered = False
    if ela_anomaly > config.ELA_TAMPERING_THRESHOLD:
        ela_triggered = True
        final_ai_risk += config.ELA_PENALTY_WEIGHT
        AuditLogger.log_trace(analysis_id, "ELAPenalty", {"ela_score": ela_anomaly}, level="WARN")

    # --- 局部篡改加性扣分（痛点3：救回"半真半假"）---
    # 局部证据不能进全局平均，否则会被大片真实区稀释。这里按强度叠加。
    local_tamper_triggered = False
    if local_tamper > config.LOCAL_TAMPER_THRESHOLD:
        local_tamper_triggered = True
        final_ai_risk += config.LOCAL_TAMPER_PENALTY * local_tamper
        AuditLogger.log_trace(analysis_id, "LocalTamperPenalty",
                              {"local_tamper": local_tamper, "region_ratio": anomaly_region_ratio}, level="WARN")

    final_ai_risk = min(1.0, max(0.0, final_ai_risk))

    v3_data = {
        "generator_signature": round(generator_signature, 3),
        "structural_collapse": round(structural_collapse, 3),
        "sensor_fake_score": round(sensor_fake_score, 3),
        "local_tampering": round(local_tamper, 3),
        "anomaly_region_ratio": round(anomaly_region_ratio, 3),
        "auxiliary_flags": {
            "ela_anomaly": round(ela_anomaly, 3),
            "over_sharpening": round(over_sharpening, 3),
            "grid_periodicity": round(grid_periodicity, 3),
        },
        "vlm_signatures": {
            "flux_signature": round(flux_sig, 3),
            "midjourney_signature": round(mj_sig, 3),
            "stable_diffusion_signature": round(sd_sig, 3),
        },
        "conflict_detected": conflict_detected,
        "conflict_msg": conflict_msg,
        "ela_triggered": ela_triggered,
        "local_tamper_triggered": local_tamper_triggered,
        "system_degraded": system_degraded,
    }

    relation_triggers = []
    if ela_triggered:
        relation_triggers.append(f"【修图警报】ELA发现局部修图/拼接痕迹 (强度: {ela_anomaly:.2f})，已作为辅助证据扣分。")
    if local_tamper_triggered:
        relation_triggers.append(
            f"【局部篡改警报】检测到与宿主图噪声底显著不同的连贯异常区 (强度: {local_tamper:.2f}，异常区占比: {anomaly_region_ratio:.2f})，"
            f"疑似局部AI重绘/扩图，已叠加扣分。")
    if system_degraded:
        relation_triggers.append("【系统故障】所有探测器传感器失效或被熔断，无法计算AI置信度，当前风险值仅作兜底参考。")
    if generator_signature > 0.6:
        relation_triggers.append(f"检测到强烈的AI模型特征指纹 (强度: {generator_signature:.2f})。")
    if grid_periodicity > 0.5:
        relation_triggers.append(f"检测到上采样栅格周期性伪影 (强度: {grid_periodicity:.2f})，疑似扩散/GAN生成。")
    if structural_collapse > 0.5:
        relation_triggers.append("检测到局部空间结构崩塌（如边缘强制融合）。")
    if sensor_fake_score > 0.6:
        relation_triggers.append("检测不到真实CMOS传感器的物理底噪。")

    for mod in degraded_modules:
        relation_triggers.append(f"⚠️ 警告：[{mod}] 探测器当前负载过高或已熔断，被系统自动跳过。本次报告仅基于剩余模块数据推演。")

    v3_data["relation_triggers"] = relation_triggers

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
        "v3_system_data": v3_data,
    }
