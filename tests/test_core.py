"""
🧪 Test Core Module
=====================
Người phụ trách: Data & Backend Lead
Mục đích: Unit test cho core/ (data_loader, schema_validator, competency_engine).
"""

import pytest
import numpy as np


class TestCompetencyEngine:
    """Test suite cho competency_engine.py."""

    def test_create_competency_vector(self):
        """Test tạo vector năng lực từ dict."""
        from src.competency_engine import create_competency_vector

        scores = {
            "sql": 7.0,
            "analytics": 5.0,
            "statistics": 8.0,
            "data_engineering": 6.0,
            "machine_learning": 4.0,
            "mlops": 3.0,
        }
        vector = create_competency_vector(scores)
        assert vector.shape == (10,)
        assert vector[0] == 7.0  # sql

    def test_identify_weak_domains(self):
        """Test xác định domain yếu."""
        from src.competency_engine import identify_weak_domains

        vector = np.array([7.0, 3.0, 8.0, 4.5, 2.0, 6.0, 7.5, 8.0, 3.5, 6.0])
        weak = identify_weak_domains(vector, threshold=5.0)
        assert "analytics" in weak
        assert "data_engineering" in weak
        assert "sql" not in weak


class TestSchemaValidator:
    """Test suite cho schema_validator.py."""

    def test_validate_valid_profile(self):
        """Test validate profile hợp lệ."""
        # TODO: Data Lead viết test
        pass

    def test_validate_invalid_profile(self):
        """Test validate profile không hợp lệ."""
        # TODO: Data Lead viết test
        pass
