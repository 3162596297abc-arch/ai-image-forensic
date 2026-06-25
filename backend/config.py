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
