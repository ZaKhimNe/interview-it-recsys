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
LLM_MODEL_NAME = "gemini-2.0-flash"
LLM_TEMPERATURE = 0.3
MAX_TOKENS = 2048

# --- Competency Domains ---
COMPETENCY_DOMAINS = [
    "Data Structures & Algorithms",
    "System Design",
    "Database & SQL",
    "OOP & Design Patterns",
    "Networking & Security",
    "DevOps & Cloud",
]
