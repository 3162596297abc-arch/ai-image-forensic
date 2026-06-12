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

ALLOWED_ORIGINS = ["*"]
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
