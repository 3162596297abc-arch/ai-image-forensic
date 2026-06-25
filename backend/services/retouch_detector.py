"""Layer 4: 辅助修图检测 — ELA 误差级别分析（v4 重构）。

关键修复：改用 raw_bgr（从原始上传字节解码的原生中心裁块）。
旧版被喂的是预处理后的 PNG，原始 JPEG 压缩历史已被抹平，ELA 形同虚设；
现在用原生像素，拼接/重绘区与宿主图的压缩响应差异才能显现。ELA 仍作为弱辅助证据。
"""
from io import BytesIO
from PIL import Image
import numpy as np
import cv2


def analyze(views: dict) -> list:
    bgr = views.get("raw_bgr")
    if bgr is None:
        bgr = views.get("proc_bgr")
    if bgr is None:
        return _fallback()

    try:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        buffer = BytesIO()
        pil.save(buffer, "JPEG", quality=90)
        buffer.seek(0)
        compressed = Image.open(buffer)
        arr_orig = np.asarray(pil).astype(np.float32)
        arr_comp = np.asarray(compressed).astype(np.float32)
    except Exception:
        return _fallback()

    if arr_orig.shape != arr_comp.shape:
        return _fallback()

    diff = np.abs(arr_orig - arr_comp)
    diff_gray = diff.mean(axis=2) if diff.ndim == 3 else diff

    max_diff = float(np.max(diff_gray))
    ela_norm = (diff_gray / max_diff) * 255.0 if max_diff > 0 else diff_gray

    h, w = diff_gray.shape
    step = max(1, max(h, w) // 16)
    patch_means = []
    for y in range(0, h - step + 1, step):
        for x in range(0, w - step + 1, step):
            patch_means.append(float(np.mean(ela_norm[y:y + step, x:x + step])))
    if not patch_means:
        return _fallback()

    ela_std = float(np.std(patch_means))
    ela_anomaly = 0.0
    if ela_std > 50.0:
        ela_anomaly = 0.4
    if ela_std > 80.0:
        ela_anomaly = 0.6

    over_sharpening = _oversharp_cv(diff_gray.astype(np.uint8))

    return [
        {"signal_name": "ela_anomaly", "signal_strength": round(ela_anomaly, 3),
         "signal_type": "edit", "confidence": 0.5, "source": "retouch"},
        {"signal_name": "over_sharpening", "signal_strength": round(over_sharpening, 3),
         "signal_type": "edit", "confidence": 0.5, "source": "retouch"},
    ]


def _oversharp_cv(gray: np.ndarray) -> float:
    """过度锐化：拉普拉斯过零密度。"""
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    if lap.shape[1] < 2:
        return 0.0
    sign = np.sign(lap[:, 1:] * lap[:, :-1])
    zero_crossings = float(np.sum(sign < 0))
    density = zero_crossings / float(gray.size)
    return 0.5 if density > 0.2 else 0.0


def _fallback() -> list:
    return [{"signal_name": "error", "signal_strength": 0.0,
             "signal_type": "error", "confidence": 0.0, "source": "retouch"}]
