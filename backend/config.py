import os
from pathlib import Path
from dotenv import load_dotenv

# Load from project root (parent of backend/)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# HuggingFace — accept both KEY and TOKEN variants
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_KEY") or os.getenv(
    "HUGGINGFACE_API_TOKEN", ""
)
HUGGINGFACE_API_URL = os.getenv(
    "HUGGINGFACE_API_URL",
    "https://api-inference.huggingface.co/models/Nahrawy/AIorNot",
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv(
    "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"
)

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_API_URL = os.getenv(
    "QWEN_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-vl-max")

# CORS — comma-separated allowlist (env: ALLOWED_ORIGINS).
# 默认只允许正式前端域名 + 本地开发，已是收紧状态（非 "*"）。
# 注意：Origin 头不含结尾斜杠，故域名不要写 "/"。
# 需要新增域名时设置环境变量覆盖，例如：
#   ALLOWED_ORIGINS=https://ai-image-forensic.vercel.app,https://your-custom-domain.com
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://ai-image-forensic.vercel.app,http://localhost:3000",
    ).split(",")
    if o.strip()
]

# Server bind — defaults to loopback (safe by default).
# Set HOST=0.0.0.0 only when running behind a reverse proxy / in a container.
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# --- Truth Engine Production Phase 1 Config ---

# Dynamic Fusion Weights
WEIGHT_GENERATOR_SIG = float(os.getenv("WEIGHT_GENERATOR_SIG", "0.40"))
WEIGHT_STRUCTURAL_COLLAPSE = float(os.getenv("WEIGHT_STRUCTURAL_COLLAPSE", "0.35"))
WEIGHT_SENSOR_REALITY = float(os.getenv("WEIGHT_SENSOR_REALITY", "0.25"))

# Conflict Arbitration
CONFLICT_THRESHOLD = float(os.getenv("CONFLICT_THRESHOLD", "0.30"))

# ELA Additive Penalty
ELA_TAMPERING_THRESHOLD = float(os.getenv("ELA_TAMPERING_THRESHOLD", "0.35"))
ELA_PENALTY_WEIGHT = float(os.getenv("ELA_PENALTY_WEIGHT", "0.15"))

# ============================================================
# Truth Engine v4 — 算法调优参数（全部可经环境变量覆盖，便于回归后微调）
# ============================================================

# --- 预处理 ---
# 给「怕压缩/缩放伪影」的模块（FFT/边缘）喂降采样版；
# 给「需要原始物理信号」的模块（CMOS底噪/ELA/栅格/元数据）喂原图中心裁块。
PROC_MAX_SIDE = int(os.getenv("PROC_MAX_SIDE", "1024"))   # 降采样视图最长边
RAW_MAX_SIDE = int(os.getenv("RAW_MAX_SIDE", "1024"))     # 原始信号视图：原生中心裁块上限（裁剪不重采样，保噪声）

# --- FFT 频域异常（痛点1：抗压缩误判）---
# 用「相对显著性」(MAD) 检测窄带周期峰；压缩的平滑衰减不会触发。
FFT_SPIKE_MAD_K = float(os.getenv("FFT_SPIKE_MAD_K", "5.0"))   # 尖峰需高于基线 K 倍 MAD
FFT_SCORE_GAIN = float(os.getenv("FFT_SCORE_GAIN", "12.0"))    # 尖峰占比 → 分数 的增益

# --- 边缘崩塌（痛点1：按边缘密度归一化，消除"细节多=误判"）---
EDGE_CORNER_PER_EDGE_THRESH = float(os.getenv("EDGE_CORNER_PER_EDGE_THRESH", "0.55"))

# --- 栅格周期性自相关（痛点2：抗压缩失效仍能抓扩散/GAN上采样栅格）---
GRID_PERIODICITY_FLOOR = float(os.getenv("GRID_PERIODICITY_FLOOR", "0.06"))
GRID_PERIODICITY_SPAN = float(os.getenv("GRID_PERIODICITY_SPAN", "0.25"))

# --- CMOS 底噪（痛点1：软化，避免降噪/缩放后的真图被强判）---
CMOS_NOISE_LOW = float(os.getenv("CMOS_NOISE_LOW", "0.6"))    # 低于此视为"异常平滑"
CMOS_NOISE_HIGH = float(os.getenv("CMOS_NOISE_HIGH", "12.0")) # 高于此视为"明显有噪=真"

# --- 局部篡改（痛点3：块级噪声异常 + 空间聚集）---
LOCAL_TAMPER_BLOCK = int(os.getenv("LOCAL_TAMPER_BLOCK", "32"))       # 网格块边长(px)
LOCAL_TAMPER_Z = float(os.getenv("LOCAL_TAMPER_Z", "3.5"))           # 稳健 z 分数离群阈值
LOCAL_TAMPER_MIN_REGION = int(os.getenv("LOCAL_TAMPER_MIN_REGION", "4"))  # 最小连通异常块数（防纹理散点）
LOCAL_TAMPER_GAIN = float(os.getenv("LOCAL_TAMPER_GAIN", "6.0"))     # 异常区占比 → 分数 的增益
LOCAL_TAMPER_THRESHOLD = float(os.getenv("LOCAL_TAMPER_THRESHOLD", "0.40"))  # 触发加性扣分阈值（留余量避开颗粒噪声）
LOCAL_TAMPER_PENALTY = float(os.getenv("LOCAL_TAMPER_PENALTY", "0.45"))      # 半真半假加性扣分上限
