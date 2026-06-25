"""共享图像解码与视图构建工具。

核心目的：把「预处理」解耦——
  - proc 视图：降采样版（INTER_AREA 抗锯齿），喂给怕压缩/缩放伪影的模块（FFT/边缘）。
  - raw  视图：原生分辨率中心裁块（只裁剪、不重采样），保住 CMOS 底噪/压缩历史/栅格，
               喂给 CMOS、ELA、栅格周期、局部篡改等需要真实物理信号的模块。

所有函数都防御式编写：解码失败、零尺寸、单通道、超大图都不会抛异常，返回 None 由调用方兜底。
"""
import numpy as np
import cv2


def _decode(image_bytes: bytes):
    """bytes -> BGR uint8 (始终 3 通道) 或 None。"""
    try:
        if not image_bytes:
            return None
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None or bgr.size == 0 or bgr.ndim != 3:
            return None
        return bgr
    except Exception:
        return None


def _downscale_area(bgr: np.ndarray, max_side: int) -> np.ndarray:
    """超过 max_side 时用 INTER_AREA 抗锯齿降采样（最适合下采样，抑制摩尔纹假峰）。"""
    h, w = bgr.shape[:2]
    longest = max(h, w)
    if longest <= max_side:
        return bgr
    scale = max_side / float(longest)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_AREA)


def _center_crop(bgr: np.ndarray, max_side: int) -> np.ndarray:
    """超过 max_side 时取中心裁块（不重采样，完整保留原生噪声/压缩块）。"""
    h, w = bgr.shape[:2]
    ch = min(h, max_side)
    cw = min(w, max_side)
    y0 = (h - ch) // 2
    x0 = (w - cw) // 2
    return bgr[y0:y0 + ch, x0:x0 + cw]


def _to_gray(bgr):
    if bgr is None:
        return None
    try:
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    except Exception:
        return None


def build_views(proc_bytes: bytes, raw_bytes: bytes,
                proc_max_side: int = 1024, raw_max_side: int = 1024) -> dict:
    """构建供所有 jury 模块共享的多视图字典（每个视图只解码一次）。

    返回 dict 键：
      proc_bgr, proc_gray  —— 降采样视图（可能为 None）
      raw_bgr,  raw_gray   —— 原生中心裁块视图（可能为 None）
      raw_bytes            —— 原始字节（供 ELA/EXIF 直接读取）
    """
    proc_bgr = _decode(proc_bytes)
    if proc_bgr is not None:
        proc_bgr = _downscale_area(proc_bgr, proc_max_side)

    raw_bgr = _decode(raw_bytes)
    if raw_bgr is not None:
        raw_bgr = _center_crop(raw_bgr, raw_max_side)

    # 兜底：任一视图解码失败时，用另一个视图顶上，保证模块至少有数据可算
    if proc_bgr is None and raw_bgr is not None:
        proc_bgr = _downscale_area(raw_bgr, proc_max_side)
    if raw_bgr is None and proc_bgr is not None:
        raw_bgr = proc_bgr

    return {
        "proc_bgr": proc_bgr,
        "proc_gray": _to_gray(proc_bgr),
        "raw_bgr": raw_bgr,
        "raw_gray": _to_gray(raw_bgr),
        "raw_bytes": raw_bytes if raw_bytes else proc_bytes,
    }
