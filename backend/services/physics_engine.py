"""Layer 2: 传感器真实性建模（v4 重构）。

使用 raw_gray（原生中心裁块视图）——CMOS 底噪是高频信号，绝不能用降采样视图，
否则 BILINEAR/AREA 会把底噪抹掉，导致真实照片被判"无底噪 = AI"（旧版最大假阳性来源）。
"""
import numpy as np
import cv2
import config


def analyze(views: dict) -> list:
    gray = views.get("raw_gray")
    if gray is None:
        gray = views.get("proc_gray")
    if gray is None:
        return _fallback()

    try:
        cmos_absence = _analyze_cmos_noise(gray)
        randomness_absence = _analyze_sensor_randomness(gray)
        lens_blur_anomaly = _analyze_lens_blur(gray)
    except Exception:
        return _fallback()

    return [
        {"signal_name": "cmos_noise_absence", "signal_strength": round(float(cmos_absence), 3),
         "signal_type": "sensor", "confidence": 0.7, "source": "physics"},
        {"signal_name": "sensor_randomness_absence", "signal_strength": round(float(randomness_absence), 3),
         "signal_type": "sensor", "confidence": 0.55, "source": "physics"},
        {"signal_name": "lens_blur_anomaly", "signal_strength": round(float(lens_blur_anomaly), 3),
         "signal_type": "sensor", "confidence": 0.5, "source": "physics"},
    ]


def _lag1_correlation(resid: np.ndarray) -> float:
    """残差水平 lag-1 归一化相关。真传感器噪声空间近白(≈0)；过平滑/AI 残差相关高。"""
    a = resid[:, :-1].ravel().astype(np.float64)
    b = resid[:, 1:].ravel().astype(np.float64)
    a -= a.mean()
    b -= b.mean()
    denom = np.sqrt(np.sum(a * a)) * np.sqrt(np.sum(b * b)) + 1e-9
    return float(abs(np.sum(a * b) / denom))


def _analyze_cmos_noise(gray: np.ndarray) -> float:
    """真实照片有高频 CMOS 底噪；AI 在数学上过于平滑。
    软化处理：低噪本身只是弱证据（手机 ISP 降噪很常见），需残差空间相关性二次确认。"""
    g = gray.astype(np.float32)
    blur = cv2.GaussianBlur(g, (5, 5), 0)
    resid = g - blur
    noise_var = float(np.var(resid))

    low, high = config.CMOS_NOISE_LOW, config.CMOS_NOISE_HIGH
    if noise_var >= high:
        base = 0.05                       # 明显有噪 = 真实
    elif noise_var <= low:
        base = 0.60                       # 异常平滑（上限 0.6，不单独强判）
    else:
        base = 0.60 * (1.0 - (noise_var - low) / (high - low))

    # 二次确认：噪声低 + 残差空间高度相关 → 更像 AI 平滑；噪声低但残差白 → 可能只是降噪真图
    if base > 0.30:
        corr = _lag1_correlation(resid)
        if corr > 0.5:
            base = min(0.80, base + 0.15)
    return max(0.0, min(1.0, base))


def _analyze_sensor_randomness(gray: np.ndarray) -> float:
    """用拉普拉斯高频的峰度(kurtosis)衡量噪声分布，数值稳定（替代旧版 var/|mean| 的爆炸式 CV）。
    真实传感器噪声峰度适中；极度均匀化或人工尖锐都偏离。弱信号、低置信。"""
    lap = cv2.Laplacian(gray.astype(np.float32), cv2.CV_64F).ravel()
    lap -= lap.mean()
    var = float(np.mean(lap * lap))
    if var < 1e-6:
        return 0.7  # 完全无高频 = 过度平滑
    kurt = float(np.mean(lap ** 4) / (var * var))  # 正态 ≈ 3
    if kurt < 1.8:
        return 0.5  # 过于均匀
    if kurt > 25.0:
        return 0.3  # 异常尖锐
    return 0.1


def _analyze_lens_blur(gray: np.ndarray) -> float:
    """景深一致性。已删除旧版"平坦图(ratio<0.2)→0.7"的假阳性分支
    （蓝天/白墙/文档照天然平坦，不是 AI 证据）。仅保留极端"超锐主体+完美糊背景"。"""
    h = gray.shape[0]
    zones = [gray[0:h // 3, :], gray[h // 3:2 * h // 3, :], gray[2 * h // 3:, :]]
    vs = []
    for z in zones:
        if z.size > 0:
            vs.append(float(np.var(cv2.Laplacian(z.astype(np.float32), cv2.CV_64F))))
    if len(vs) < 2:
        return 0.0
    mean_v = float(np.mean(vs)) + 1e-5
    ratio = float(np.std(vs)) / mean_v
    if ratio > 2.0:
        return min(0.6, 0.3 + (ratio - 2.0) / 2.0)
    return 0.0


def _fallback() -> list:
    return [{"signal_name": "error", "signal_strength": 0.0,
             "signal_type": "error", "confidence": 0.0, "source": "physics"}]
