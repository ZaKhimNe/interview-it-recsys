"""
⚙️ Global Configuration
========================
Người phụ trách: Shared (cả 3 Lead đều có thể cập nhật)
Mục đích: Tập trung quản lý hằng số, đường dẫn, và cấu hình chung.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
DATA_DIR = os.getenv("DATA_DIR", "data/")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "data/vector_store/")

# --- API Keys ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# --- App Settings ---
APP_ENV = os.getenv("APP_ENV", "development")
APP_DEBUG = os.getenv("APP_DEBUG", "true").lower() == "true"

# --- AI Settings ---
LLM_MODEL_NAME = "gemini-3.5-flash"
LLM_TEMPERATURE = 0.3
MAX_TOKENS = 2048

# --- API Server ---
API_PORT = int(os.getenv("API_PORT", "8000"))

# --- Knowledge Component Taxonomy ---
# 17 KCs shared across all roles; maps role -> KC list (uppercase, matches metadata.json)
KC_BY_ROLE = {
    "DA": [
        "SQL_DATABASE",
        "BI_VISUALIZATION",
        "STATISTICS_EXPERIMENTATION",
        "ANALYTICS_BUSINESS",
        "PYTHON_ANALYTICS",
    ],
    "DS": [
        "ALGORITHM_THEORY",
        "EVALUATION_METRICS",
        "DATA_PREPROCESSING",
        "DEEP_LEARNING",
        "NLP",
        "TIME_SERIES",
        "MLOPS",
    ],
    "DE": [
        "DATA_PIPELINE",
        "DATA_ARCHITECTURE_MODELING",
        "BIG_DATA_CLOUD_TOOLS",
        "DATABASE_INTERNALS",
        "SYSTEM_ARCHITECTURE",
    ],
}

# Flat list of all 17 KCs (used by KT models)
ALL_KCS = [kc for kcs in KC_BY_ROLE.values() for kc in kcs]

# Legacy alias — kept for backward-compat
COMPETENCY_DOMAINS = ALL_KCS
