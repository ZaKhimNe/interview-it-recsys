"""
📋 Logger Configuration
========================
Người phụ trách: Shared
Mục đích: Cấu hình logging tập trung cho toàn bộ dự án.
          Sử dụng loguru để ghi log có cấu trúc.
"""

from loguru import logger
import sys

# Xóa handler mặc định
logger.remove()

# Console handler (development)
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    colorize=True,
)

# File handler (production)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
)


def get_logger(module_name: str):
    """Lấy logger instance cho module cụ thể."""
    return logger.bind(name=module_name)
