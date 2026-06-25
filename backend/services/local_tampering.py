"""Layer 5: 局部篡改检测（v4 新增，针对痛点3：真底图 + 局部 AI 重绘/扩图）。

思路：全局统计会被大片真实区稀释，所以改用「空间分块 + 噪声底分布」：
  1. 在 raw（原生）视图上算高通噪声残差，按 32×32 网格求每块噪声底。
  2. 用稳健统计(中位/MAD)算每块的 z 分数——拼接/重绘区的噪声底会系统性偏离宿主图。
  3. 连通域要求空间聚集（避免把纹理散点误判）；
     再用"异常区占比"把"小而连贯的篡改块"识别出来（占比过半更像场景构成，降权）。
输出 local_tampering（主）+ anomaly_region_ratio（辅）。
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
        score, region_ratio = _detect(gray)
    except Exception:
        return _fallback()

    return [
        {"signal_name": "local_tampering", "signal_strength": round(float(score), 3),
         "signal_type": "spatial", "confidence": 0.65, "source": "local"},
        {"signal_name": "anomaly_region_ratio", "signal_strength": round(float(region_ratio), 3),
         "signal_type": "spatial", "confidence": 0.5, "source": "local"},
    ]


def _detect(gray: np.ndarray) -> tuple:
    g = gray.astype(np.float32)
    h, w = g.shape
    bs = max(8, config.LOCAL_TAMPER_BLOCK)
    nby, nbx = h // bs, w // bs
    if nby < 4 or nbx < 4:
        return 0.0, 0.0  # 太小，空间分析不可靠

    # 高通噪声残差 → 每块噪声底（均值）
    blur = cv2.GaussianBlur(g, (3, 3), 0)
    resid = np.abs(g - blur)
    block = np.empty((nby, nbx), np.float32)
    for by in range(nby):
        ys = by * bs
        for bx in range(nbx):
            xs = bx * bs
            block[by, bx] = float(resid[ys:ys + bs, xs:xs + bs].mean())

    # 稳健 z 分数（中位 + MAD），对离群不敏感，能稳定刻画"与宿主图不同的噪声底"
    med = float(np.median(block))
    mad = float(np.median(np.abs(block - med))) + 1e-6
    z = np.abs(block - med) / (1.4826 * mad)
    anomaly = (z > config.LOCAL_TAMPER_Z).astype(np.uint8)
    region_ratio = float(anomaly.mean())
    if int(anomaly.sum()) == 0:
        return 0.0, 0.0

    # 空间聚集：最大连通异常区（8 邻接）。散点(纹理) → largest 小 → 不算篡改。
    n_labels, _, stats, _ = cv2.connectedComponentsWithStats(anomaly, connectivity=8)
    largest = int(stats[1:, cv2.CC_STAT_AREA].max()) if n_labels > 1 else 0
    if largest < config.LOCAL_TAMPER_MIN_REGION:
        return 0.0, region_ratio

    largest_ratio = largest / float(nby * nbx)
    # 占比过半更像"场景构成"(天空/地面噪声本就不同)，而非局部篡改 → 降权
    coherence = 1.0 if largest_ratio <= 0.5 else max(0.0, 1.0 - (largest_ratio - 0.5) / 0.5)
    score = min(1.0, largest_ratio * config.LOCAL_TAMPER_GAIN) * coherence
    return float(score), float(region_ratio)


def _fallback() -> list:
    return [{"signal_name": "error", "signal_strength": 0.0,
             "signal_type": "error", "confidence": 0.0, "source": "local"}]
