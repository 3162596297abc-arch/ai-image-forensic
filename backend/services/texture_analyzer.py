"""Layer 3: 结构崩塌 + 频域/栅格异常检测（v4 重构）。

输入：views 字典（见 services/imaging.build_views）。
  - FFT / 边缘 / 重复  使用 proc_gray（降采样视图，抗压缩缩放伪影）。
  - 栅格周期性自相关    使用 raw_gray（原生中心裁块，保住扩散/GAN 上采样栅格）。
"""
import numpy as np
import cv2
import config


def analyze(views: dict) -> list:
    proc_gray = views.get("proc_gray")
    raw_gray = views.get("raw_gray")

    if proc_gray is None and raw_gray is None:
        return _fallback()
    if proc_gray is None:
        proc_gray = raw_gray

    try:
        fft_anomaly = _analyze_fft_anomalies(proc_gray)
        edge_collapse = _analyze_edge_collapse(proc_gray)
        local_repetition = _analyze_repetition(proc_gray)
    except Exception:
        fft_anomaly = edge_collapse = local_repetition = 0.0

    try:
        grid_periodicity = _analyze_grid_periodicity(
            raw_gray if raw_gray is not None else proc_gray
        )
    except Exception:
        grid_periodicity = 0.0

    # 弱信号挤压：避免商业摄影的轻微特征触发误判
    fft_anomaly = fft_anomaly if fft_anomaly > 0.55 else 0.0
    edge_collapse = edge_collapse if edge_collapse > 0.55 else 0.0
    local_repetition = local_repetition if local_repetition > 0.6 else 0.0
    grid_periodicity = grid_periodicity if grid_periodicity > 0.5 else 0.0

    return [
        {"signal_name": "fft_abnormal_spikes", "signal_strength": round(float(fft_anomaly), 3),
         "signal_type": "structure", "confidence": 0.75, "source": "texture"},
        {"signal_name": "edge_collapse", "signal_strength": round(float(edge_collapse), 3),
         "signal_type": "structure", "confidence": 0.65, "source": "texture"},
        {"signal_name": "local_repetition", "signal_strength": round(float(local_repetition), 3),
         "signal_type": "structure", "confidence": 0.45, "source": "texture"},
        {"signal_name": "grid_periodicity", "signal_strength": round(float(grid_periodicity), 3),
         "signal_type": "structure", "confidence": 0.8, "source": "texture"},
    ]


# ---------------------------------------------------------------------------
# 1) FFT 频域异常：径向功率谱 + 相对显著性(MAD) 检测窄带周期峰
#    原理：JPEG 压缩 / 缩放只会让径向谱"平滑衰减"——去趋势后没有尖峰；
#         GAN/Diffusion 的上采样会在固定频率留下"窄带尖峰"——去趋势后凸出。
#    用 np.bincount 向量化（替代原 O(R·H·W) 的 Python 循环，提速约 100×）。
# ---------------------------------------------------------------------------
def _radial_profile(mag: np.ndarray) -> np.ndarray:
    h, w = mag.shape
    cy, cx = h // 2, w // 2
    y, x = np.indices((h, w))
    r = np.hypot(x - cx, y - cy).astype(np.int32)
    tbin = np.bincount(r.ravel(), weights=mag.ravel())
    nr = np.bincount(r.ravel())
    return tbin / np.maximum(nr, 1)


def _median_filter_1d(a: np.ndarray, k: int) -> np.ndarray:
    if k < 3:
        return a.copy()
    if k % 2 == 0:
        k += 1
    pad = k // 2
    ap = np.pad(a, pad, mode="edge")
    out = np.empty_like(a)
    for i in range(a.shape[0]):
        out[i] = np.median(ap[i:i + k])
    return out


def _analyze_fft_anomalies(gray: np.ndarray) -> float:
    g = gray.astype(np.float32)
    f = np.fft.fftshift(np.fft.fft2(g))
    mag = np.log1p(np.abs(f))
    radial = _radial_profile(mag)
    n = radial.shape[0]
    if n < 24:
        return 0.0
    # 只看中高频环：低频被画面内容能量主导，最高频是边界噪声
    lo, hi = int(n * 0.18), int(n * 0.92)
    seg = radial[lo:hi]
    if seg.shape[0] < 12:
        return 0.0
    # 去趋势：减掉平滑基线（压缩的平滑衰减被消掉）
    base = _median_filter_1d(seg, max(3, (seg.shape[0] // 16) | 1))
    resid = seg - base
    mad = np.median(np.abs(resid - np.median(resid))) + 1e-6
    spikes = resid > (config.FFT_SPIKE_MAD_K * mad)
    spike_ratio = float(np.count_nonzero(spikes)) / float(seg.shape[0])
    return min(1.0, spike_ratio * config.FFT_SCORE_GAIN)


# ---------------------------------------------------------------------------
# 2) 边缘崩塌：角点数按"边缘像素"归一化（而非总像素），消除"细节多→误判"
# ---------------------------------------------------------------------------
def _analyze_edge_collapse(gray: np.ndarray) -> float:
    h, w = gray.shape
    if h < 48 or w < 48:
        return 0.0  # 太小，无从判断
    # 关键：先中值去噪，消除高ISO/胶片颗粒产生的"伪角点"。
    # 否则真实grainy照片会被 Harris 误判出海量杂乱角点 → edge_collapse 假阳性。
    g = cv2.medianBlur(gray, 3)
    edges = cv2.Canny(g, 50, 150)
    edge_pixels = int(np.count_nonzero(edges))
    if edge_pixels < 200:
        return 0.0  # 边缘太少，无从判断
    # 极高边缘密度 = 噪声/纹理主导，角点指标不可靠 → 不判
    if edge_pixels / float(gray.size) > 0.40:
        return 0.0
    harris = cv2.cornerHarris(np.float32(g), 2, 3, 0.04)
    hmax = float(harris.max())
    if hmax <= 0:
        return 0.0
    corners = int(np.count_nonzero(harris > 0.01 * hmax))
    # 关键归一化：每单位边缘长度上的角点数。
    # 真实照片边缘平直，角点/边缘比适中；AI"强制融合"会在边缘上堆大量杂乱角点。
    corner_per_edge = corners / float(edge_pixels)
    thresh = config.EDGE_CORNER_PER_EDGE_THRESH
    if corner_per_edge <= thresh:
        return 0.0
    return min(1.0, (corner_per_edge - thresh) / max(thresh, 1e-6))


# ---------------------------------------------------------------------------
# 3) 局部重复纹理：块方差的变异系数过低 = 人工重复
# ---------------------------------------------------------------------------
def _analyze_repetition(gray: np.ndarray) -> float:
    h, w = gray.shape
    if h < 48 or w < 48:
        return 0.0  # 太小，无法评估
    bh = max(8, h // 8)
    bw = max(8, w // 8)
    blocks = []
    for y in range(0, h - bh + 1, bh):
        for x in range(0, w - bw + 1, bw):
            blocks.append(float(np.var(gray[y:y + bh, x:x + bw])))
    if len(blocks) < 8:
        return 0.0
    mean_var = float(np.mean(blocks))
    # 关键守卫：几乎无纹理（纯色/平坦/文档/纯背景）→ 块方差全≈0，
    # 旧版会误判成"极端重复"。这类图无从判定重复，直接返回 0，消除一大类假阳性。
    if mean_var < 8.0:
        return 0.0
    cv_val = float(np.std(blocks)) / (mean_var + 1e-5)
    # 仅在"块方差极度均匀"时触发（人工重复纹理），阈值收紧到 0.12，弱信号低置信
    if cv_val < 0.12:
        return 0.8
    return 0.0


# ---------------------------------------------------------------------------
# 4) 栅格周期性（痛点2 新增）：高通残差的归一化自相关
#    原理：真实传感器噪声在空间上近似"白噪声"——自相关只有中心一个尖峰，旁瓣≈0。
#         扩散/GAN 的上采样会引入固定步长栅格——自相关在小位移处出现明显次峰。
#    在 raw（原生）视图上算，避免降采样把栅格抹掉。内容无关，ELA/底噪失效时仍有效。
# ---------------------------------------------------------------------------
def _analyze_grid_periodicity(gray: np.ndarray) -> float:
    g = gray.astype(np.float32)
    if min(g.shape) < 64:
        return 0.0
    blur = cv2.GaussianBlur(g, (3, 3), 0)
    resid = g - blur
    resid -= float(resid.mean())
    F = np.fft.fft2(resid)
    ac = np.fft.ifft2(F * np.conj(F)).real
    ac = np.fft.fftshift(ac)
    peak = float(ac.max())
    if peak <= 0:
        return 0.0
    ac /= peak
    h, w = ac.shape
    cy, cx = h // 2, w // 2
    win = 24
    region = ac[max(0, cy - win):cy + win + 1, max(0, cx - win):cx + win + 1].copy()
    if region.size == 0:
        return 0.0
    ry, rx = region.shape[0] // 2, region.shape[1] // 2
    # 抹掉中心尖峰及其紧邻（去掉自相关的 delta），只看次峰
    region[max(0, ry - 1):ry + 2, max(0, rx - 1):rx + 2] = 0.0
    secondary = float(region.max())  # 0..1
    floor, span = config.GRID_PERIODICITY_FLOOR, config.GRID_PERIODICITY_SPAN
    return float(min(1.0, max(0.0, (secondary - floor) / max(span, 1e-6))))


def _fallback() -> list:
    return [{"signal_name": "error", "signal_strength": 0.0,
             "signal_type": "error", "confidence": 0.0, "source": "texture"}]
