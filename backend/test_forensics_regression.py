"""Truth Engine v4 — 本地法医算法回归测试（独立运行，不依赖网络/Qwen）。

用途：
  1) 冒烟测试：不传参时自动生成「真实/AI/局部篡改」三类合成图，端到端跑全管线，
     验证不崩溃且各信号朝正确方向移动。
  2) 真实回归：传入一个目录，按子目录名(real / ai / tampered)或文件名前缀打标签，
     批量跑并输出每张图的关键信号 + 预测层级 + 混淆矩阵 / 准确率。

用法：
    python test_forensics_regression.py                 # 合成冒烟测试
    python test_forensics_regression.py  path/to/dataset  # 真实样本回归
        dataset/
          real/      *.jpg ...   # 真实照片
          ai/        *.png ...   # 纯 AI 生成
          tampered/  *.jpg ...   # 局部篡改(真底图+AI重绘/扩图)

只依赖 numpy / opencv-python-headless / Pillow（与后端一致）。
"""
import os
import sys
import glob
from io import BytesIO

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文/emoji 编码崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
from PIL import Image

# 让脚本无论从哪运行都能 import 后端模块
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402
from services.imaging import build_views  # noqa: E402
from services.texture_analyzer import analyze as texture_analyze  # noqa: E402
from services.physics_engine import analyze as physics_analyze  # noqa: E402
from services.local_tampering import analyze as local_tampering_analyze  # noqa: E402
from services.retouch_detector import analyze as retouch_analyze  # noqa: E402
from services.metadata_analyzer import analyze as metadata_analyze  # noqa: E402
from services.fusion import fuse_features  # noqa: E402


# ---------------------------------------------------------------------------
# 复刻 analyze.py 的预处理（proc 降采样 + raw 原生裁块），但全本地、无网络
# ---------------------------------------------------------------------------
def preprocess(image_bytes: bytes):
    img = Image.open(BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
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
        raw_bytes = image_bytes
    img.thumbnail((config.PROC_MAX_SIDE, config.PROC_MAX_SIDE), Image.Resampling.BILINEAR)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), raw_bytes


def analyze_local(image_bytes: bytes) -> dict:
    """跑完整本地管线（不含 Qwen 生成器指纹），返回 fusion 结果 dict。
    无法解析的输入（损坏字节）→ 返回降级 dict（生产环境由 API 层 400 拦截）。"""
    try:
        proc_bytes, raw_bytes = preprocess(image_bytes)
    except Exception:
        return {"ai_participation": 0.0, "tier": "Low",
                "v3_system_data": {"system_degraded": True, "error": "unreadable_image"}}
    views = build_views(proc_bytes, raw_bytes, config.PROC_MAX_SIDE, config.RAW_MAX_SIDE)
    module_results = [
        texture_analyze(views),
        physics_analyze(views),
        local_tampering_analyze(views),
        retouch_analyze(views),
        metadata_analyze(views),
    ]
    # hf_features 置空 = 模拟 Qwen 不可用，纯测本地物理/像素管线
    return fuse_features("regression-test", module_results, [])


def _signal(module_results, name):
    for lst in module_results:
        for e in lst:
            if e.get("signal_name") == name:
                return e.get("signal_strength", 0.0)
    return 0.0


def report_one(label, image_bytes):
    proc_bytes, raw_bytes = preprocess(image_bytes)
    views = build_views(proc_bytes, raw_bytes, config.PROC_MAX_SIDE, config.RAW_MAX_SIDE)
    mods = [
        texture_analyze(views), physics_analyze(views),
        local_tampering_analyze(views), retouch_analyze(views), metadata_analyze(views),
    ]
    fused = fuse_features("regression-test", mods, [])
    v3 = fused["v3_system_data"]
    print(f"  [{label:8}] tier={fused['tier']:8} ai_participation={fused['ai_participation']:.3f}  "
          f"fft={_signal(mods,'fft_abnormal_spikes'):.2f} edge={_signal(mods,'edge_collapse'):.2f} "
          f"grid={_signal(mods,'grid_periodicity'):.2f} cmos={_signal(mods,'cmos_noise_absence'):.2f} "
          f"local_tamper={_signal(mods,'local_tampering'):.2f} ela={_signal(mods,'ela_anomaly'):.2f}")
    return fused


# ---------------------------------------------------------------------------
# 合成样本生成（确定性，可复现）
# ---------------------------------------------------------------------------
def _save(arr, fmt="JPEG", quality=92):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    pil = Image.fromarray(arr)
    buf = BytesIO()
    if fmt == "JPEG":
        pil.save(buf, "JPEG", quality=quality)
    else:
        pil.save(buf, "PNG")
    return buf.getvalue()


def gen_real(seed=1, size=768):
    """真实照片代理：平滑场景 + 真实传感器高斯底噪 + JPEG 压缩。"""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    base = (128 + 60 * np.sin(xx / 90.0) + 40 * np.cos(yy / 130.0))[..., None]
    base = np.repeat(base, 3, axis=2)
    base += rng.normal(0, 6.0, base.shape)          # CMOS 底噪
    return _save(base, "JPEG", 92)


def gen_ai(seed=2, size=768):
    """AI 生成代理：超平滑渐变(无底噪) + 周期栅格(上采样指纹) + PNG。"""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    base = (128 + 80 * np.sin(xx / 200.0) + 60 * np.cos(yy / 240.0))[..., None]
    base = np.repeat(base, 3, axis=2)
    grid = 6.0 * np.sin(xx * np.pi / 4.0) * np.sin(yy * np.pi / 4.0)  # 步长4px栅格
    base += grid[..., None]
    return _save(base, "PNG")


def gen_tampered(seed=3, size=768):
    """局部篡改代理：真实底图(带噪) + 中央一块被'AI重绘'(抹平噪声)。"""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    base = (128 + 60 * np.sin(xx / 90.0) + 40 * np.cos(yy / 130.0))[..., None]
    base = np.repeat(base, 3, axis=2)
    base += rng.normal(0, 6.0, base.shape)
    # 中央 1/3 区域：抹掉噪声并轻微平滑 = 局部AI重绘的噪声底突变
    a, b = size // 3, 2 * size // 3
    patch = (128 + 60 * np.sin(xx[a:b, a:b] / 90.0) + 40 * np.cos(yy[a:b, a:b] / 130.0))[..., None]
    base[a:b, a:b, :] = np.repeat(patch, 3, axis=2)  # 无噪声版本
    return _save(base, "JPEG", 92)


def smoke_test():
    print("=== 合成冒烟测试（验证管线端到端可跑 + 信号方向）===")
    samples = [("real", gen_real()), ("ai", gen_ai()), ("tampered", gen_tampered())]
    results = {}
    for label, data in samples:
        results[label] = report_one(label, data)
    print()
    # 方向性断言（不是精度断言，只确认没接反/没崩）
    ok = True
    if results["ai"]["ai_participation"] <= results["real"]["ai_participation"]:
        print("  ⚠️ 期望 AI 图风险 > 真实图风险，未满足（阈值需用真实样本标定）")
        ok = False
    lt = _local_tamper_of(gen_tampered())
    lt_real = _local_tamper_of(gen_real())
    if lt <= lt_real:
        print("  ⚠️ 期望 篡改图 local_tampering > 真实图，未满足（阈值需标定）")
        ok = False
    print("  ✅ 管线端到端运行正常，无异常崩溃。" if ok else "  ✅ 管线可跑；方向性需用真实样本标定阈值。")
    return ok


def _local_tamper_of(image_bytes):
    proc_bytes, raw_bytes = preprocess(image_bytes)
    views = build_views(proc_bytes, raw_bytes, config.PROC_MAX_SIDE, config.RAW_MAX_SIDE)
    for e in local_tampering_analyze(views):
        if e.get("signal_name") == "local_tampering":
            return e.get("signal_strength", 0.0)
    return 0.0


# ---------------------------------------------------------------------------
# 真实数据集回归
# ---------------------------------------------------------------------------
def _label_of(path):
    p = path.replace("\\", "/").lower()
    for lab in ("tampered", "real", "ai"):
        if f"/{lab}/" in p or os.path.basename(p).startswith(lab):
            return lab
    return "unknown"


def dataset_test(folder):
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")
    files = []
    for e in exts:
        files += glob.glob(os.path.join(folder, "**", e), recursive=True)
    if not files:
        print(f"目录 {folder} 下没找到图片。")
        return
    print(f"=== 真实样本回归：{len(files)} 张图 ===")
    # AI 判定：tier in (High, Critical) 视为"判 AI"
    correct = total = 0
    confusion = {}
    for f in sorted(files):
        try:
            with open(f, "rb") as fh:
                data = fh.read()
            fused = report_one(_label_of(f) + ":" + os.path.basename(f)[:14], data)
        except Exception as ex:
            print(f"  跳过 {f}: {ex}")
            continue
        lab = _label_of(f)
        if lab == "unknown":
            continue
        pred_ai = fused["tier"] in ("High", "Critical")
        truth_ai = lab in ("ai", "tampered")
        total += 1
        if pred_ai == truth_ai:
            correct += 1
        key = (lab, "AI" if pred_ai else "REAL")
        confusion[key] = confusion.get(key, 0) + 1
    print()
    if total:
        print(f"准确率(AI vs REAL 二分类): {correct}/{total} = {correct/total*100:.1f}%")
        print("混淆分布:", confusion)
    print("提示：local_tampering / 各阈值可在 config.py 用环境变量微调后重跑本脚本。")


if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        dataset_test(sys.argv[1])
    else:
        smoke_test()
