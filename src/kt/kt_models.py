"""
kt_models.py — re-export BKT, DKT, SAKT từ kt_models/ root package.

kt_models/ nằm ở project root (cùng cấp với src/).
File này giúp src/ import được các class mà không cần thay đổi sys.path.
"""
import sys
from pathlib import Path

# Thêm project root vào sys.path để import kt_models package
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kt_models.bkt import BKT    # noqa: F401
from kt_models.dkt import DKT, DKTModel    # noqa: F401
from kt_models.sakt import SAKT, SAKTModel  # noqa: F401

__all__ = ["BKT", "DKT", "DKTModel", "SAKT", "SAKTModel"]
