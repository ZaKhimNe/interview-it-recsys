"""
KT Predictor — load trained BKT/DKT/SAKT, estimate skill per KC.

Interface chính:
    predictor = KTPredictor()
    skill_vec  = predictor.predict_skill(user_history, role)
    # -> dict[UPPERCASE_KC, float in 0.05..0.99]

user_history: list of {kc: UPPERCASE_KC, score: float 0-10, is_correct: bool}

Model mặc định: dkt_quality (best model theo ablation).
Fallback: nếu không load được model → trả về {} (caller dùng EMA).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

_logger = logging.getLogger(__name__)

_BASE_DIR    = Path(__file__).resolve().parents[2]
_MODELS_DIR  = _BASE_DIR / "results" / "models"

# Số tương tác tối thiểu để KT prediction đáng tin cậy
_MIN_HISTORY = 3


class KTPredictor:
    """
    Singleton-style predictor: load model một lần, dùng nhiều lần.

    Attributes:
        model_name: tên model trong model_configs.json
        _model    : DKT/BKT/SAKT instance đã load weights
        _kc_to_idx: {'ALGORITHM_THEORY': 0, ...}
        _idx_to_kc: {0: 'ALGORITHM_THEORY', ...}
        n_kcs     : số KC trong model (17)
    """

    _instances: dict[str, "KTPredictor"] = {}

    def __new__(cls, model_name: str = "dkt_quality"):
        if model_name not in cls._instances:
            inst = super().__new__(cls)
            inst._initialized = False
            cls._instances[model_name] = inst
        return cls._instances[model_name]

    def __init__(self, model_name: str = "dkt_quality"):
        if self._initialized:
            return
        self.model_name = model_name
        self._model     = None
        self._kc_to_idx: dict[str, int] = {}
        self._idx_to_kc: dict[int, str] = {}
        self.n_kcs      = 17
        self._initialized = True
        self._load()

    # ── Loading ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load metadata + model weights. Ghi log lỗi và tiếp tục nếu thất bại."""
        try:
            self._load_metadata()
            self._load_model()
        except Exception as e:
            _logger.warning(f"[KTPredictor] Load failed ({e}). Fallback to EMA.")
            self._model = None

    def _load_metadata(self) -> None:
        meta_path = _MODELS_DIR / "metadata.json"
        with meta_path.open("r") as f:
            meta = json.load(f)
        self.n_kcs = meta["n_kcs"]
        # kc2idx dùng lowercase keys → chuyển sang UPPERCASE
        for kc_lower, idx in meta["kc2idx"].items():
            kc_upper = kc_lower.upper()
            self._kc_to_idx[kc_upper] = idx
            self._idx_to_kc[idx] = kc_upper

    def _load_model(self) -> None:
        cfg_path = _MODELS_DIR / "model_configs.json"
        with cfg_path.open("r") as f:
            configs = json.load(f)

        cfg = configs.get(self.model_name)
        if cfg is None:
            raise ValueError(f"Model '{self.model_name}' not found in model_configs.json")

        model_file = _MODELS_DIR / cfg["file"]
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        model_type = cfg["model_type"]

        if model_type == "dkt":
            from src.kt.kt_models import DKT
            m = DKT(
                n_kcs       = cfg["n_kcs"],
                mode        = cfg["mode"],
                hidden_size = cfg["hidden_size"],
                n_layers    = cfg["n_layers"],
                dropout     = cfg["dropout"],
            )
            m.load(str(model_file))
            m.model.eval()
            self._model = m
            self._model_type = "dkt"

        elif model_type == "sakt":
            from src.kt.kt_models import SAKT
            m = SAKT(
                n_kcs     = cfg["n_kcs"],
                mode      = cfg["mode"],
                embed_dim = cfg["embed_dim"],
                n_heads   = cfg["n_heads"],
                n_layers  = cfg["n_layers"],
                dropout   = cfg["dropout"],
            )
            m.load(str(model_file))
            m.model.eval()
            self._model = m
            self._model_type = "sakt"

        elif model_type == "bkt":
            from src.kt.kt_models import BKT
            m = BKT(n_kcs=cfg["n_kcs"])
            m.load(str(model_file))
            self._model = m
            self._model_type = "bkt"

        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        _logger.info(f"[KTPredictor] Loaded {self.model_name} from {model_file}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        return self._model is not None

    def predict_skill(
        self,
        user_history: list[dict],
        role: str,
    ) -> dict[str, float]:
        """
        Ước tính skill từ lịch sử trả lời.

        Args:
            user_history: list of {kc: UPPERCASE_KC, score: float 0-10, is_correct: bool}
            role        : DA / DS / DE (để filter KC của role)

        Returns:
            dict[UPPERCASE_KC → float 0.05..0.99]
            Trả về {} nếu model không sẵn sàng hoặc history quá ngắn.
        """
        if self._model is None or len(user_history) < _MIN_HISTORY:
            return {}

        kc_seq, correct_seq, quality_seq = self._build_sequences(user_history)
        if not kc_seq:
            return {}

        try:
            if self._model_type == "dkt":
                return self._predict_dkt(kc_seq, correct_seq, quality_seq, role)
            elif self._model_type == "bkt":
                return self._predict_bkt(kc_seq, correct_seq, role)
            elif self._model_type == "sakt":
                return self._predict_sakt(kc_seq, correct_seq, role)
        except Exception as e:
            _logger.warning(f"[KTPredictor] Inference failed: {e}")

        return {}

    # ── Sequence builder ───────────────────────────────────────────────────────

    def _build_sequences(
        self,
        history: list[dict],
    ) -> tuple[list[int], list[int], list[float]]:
        """
        Chuyển user_history → (kc_seq, correct_seq, quality_seq) theo index của model.
        Bỏ qua các entry có KC không trong kc2idx.
        """
        kc_seq, correct_seq, quality_seq = [], [], []
        for entry in history:
            kc_upper = str(entry.get("kc", "")).upper()
            idx = self._kc_to_idx.get(kc_upper)
            if idx is None:
                continue
            score = float(entry.get("score", 0.0))  # 0-10
            is_correct = bool(entry.get("is_correct", score >= 6.0))
            quality_norm = min(score / 10.0, 1.0)

            kc_seq.append(idx)
            correct_seq.append(1 if is_correct else 0)
            quality_seq.append(quality_norm)

        return kc_seq, correct_seq, quality_seq

    # ── DKT inference ──────────────────────────────────────────────────────────

    def _predict_dkt(
        self,
        kc_seq: list[int],
        correct_seq: list[int],
        quality_seq: list[float],
        role: str,
    ) -> dict[str, float]:
        """
        DKT forward pass: input (1, T, 2*n_kcs) → output (1, T, n_kcs).
        Lấy last timestep output[:, -1, :] làm P(correct) cho từng KC.
        """
        import torch
        from src.kt.kt_models import DKTModel

        T = len(kc_seq)
        x = torch.zeros(1, T, 2 * self.n_kcs)
        for t, (kc, c) in enumerate(zip(kc_seq, correct_seq)):
            if c:
                x[0, t, kc] = 1.0
            else:
                x[0, t, kc + self.n_kcs] = 1.0

        device = self._model.device
        with __import__("torch").no_grad():
            output = self._model.model(x.to(device))   # (1, T, n_kcs)

        last = output[0, -1, :].cpu().numpy()  # (n_kcs,)
        return self._to_skill_dict(last, role)

    # ── BKT inference ──────────────────────────────────────────────────────────

    def _predict_bkt(
        self,
        kc_seq: list[int],
        correct_seq: list[int],
        role: str,
    ) -> dict[str, float]:
        """
        BKT Bayesian filter: chạy forward pass thủ công, lấy P(mastery) cuối cùng.
        """
        params = self._model.params  # (n_kcs, 4) in logit space
        sig = self._model._sig

        p_L = {k: sig(params[k][0]) for k in range(self.n_kcs)}
        EPS = 1e-6

        for kc, correct in zip(kc_seq, correct_seq):
            L0, T_p, S, G = (sig(params[kc][i]) for i in range(4))
            p_c = float(np.clip(p_L[kc] * (1 - S) + (1 - p_L[kc]) * G, EPS, 1 - EPS))
            y = 1 if correct else 0
            p_Lg = (p_L[kc] * (1 - S) / p_c) if y else (p_L[kc] * S / (1 - p_c))
            p_Lg = float(np.clip(p_Lg, EPS, 1 - EPS))
            p_L[kc] = p_Lg + (1 - p_Lg) * T_p

        mastery = np.array([p_L[k] for k in range(self.n_kcs)], dtype=float)
        return self._to_skill_dict(mastery, role)

    # ── SAKT inference ─────────────────────────────────────────────────────────

    def _predict_sakt(
        self,
        kc_seq: list[int],
        correct_seq: list[int],
        role: str,
    ) -> dict[str, float]:
        """
        SAKT: predict P(correct) cho từng KC bằng cách query model với
        kc_next = mỗi KC một lần, lấy giá trị tại bước cuối.
        """
        import torch

        T = len(kc_seq)
        inter = [kc if c else kc + self.n_kcs for kc, c in zip(kc_seq, correct_seq)]
        inter_t = torch.tensor(inter, dtype=torch.long).unsqueeze(0)  # (1, T)
        device  = self._model.device

        skill = np.zeros(self.n_kcs)
        with __import__("torch").no_grad():
            for kc_idx in range(self.n_kcs):
                kc_next_t = torch.full((1, T), kc_idx, dtype=torch.long)
                pred = self._model.model(
                    inter_t.to(device), kc_next_t.to(device)
                )  # (1, T)
                skill[kc_idx] = float(pred[0, -1].cpu())

        return self._to_skill_dict(skill, role)

    # ── Helper ─────────────────────────────────────────────────────────────────

    def _to_skill_dict(self, skill_array: np.ndarray, role: str) -> dict[str, float]:
        """
        Map array[n_kcs] → dict[UPPERCASE_KC → clipped float].
        Chỉ trả về KC thuộc role.
        """
        from src.kt.competency_engine import get_role_kcs
        role_kcs = set(get_role_kcs(role))
        result = {}
        for idx, val in enumerate(skill_array):
            kc = self._idx_to_kc.get(idx)
            if kc and kc in role_kcs:
                result[kc] = round(float(np.clip(val, 0.05, 0.99)), 4)
        return result


# ── Module-level convenience singleton ────────────────────────────────────────

_default_predictor: Optional[KTPredictor] = None


def get_predictor(model_name: str = "dkt_quality") -> KTPredictor:
    """Lấy singleton KTPredictor (lazy init)."""
    global _default_predictor
    if _default_predictor is None:
        _default_predictor = KTPredictor(model_name)
    return _default_predictor


def predict_skill(
    user_history: list[dict],
    role: str,
    model_name: str = "dkt_quality",
) -> dict[str, float]:
    """Shortcut function — không cần khởi tạo predictor thủ công."""
    return get_predictor(model_name).predict_skill(user_history, role)
