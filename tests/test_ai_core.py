import numpy as np

from src.grader import generate_follow_up, grade_answer
from src.recommender import COMPETENCY_KEYS, adaptive_difficulty, recommend_questions


class TestRecommender:
    def test_recommend_questions_prioritizes_weak_domain(self):
        questions = [
            {
                "question_id": "DB_001",
                "question_text": "SQL joins?",
                "difficulty_score": 2,
                "difficulty_label": "EASY",
                "skill_tags": ["SQL_JOIN"],
                "roles": {"primary": "DA"},
                "answers": {"detailed": "Use joins to combine tables."},
            },
            {
                "question_id": "DS_001",
                "question_text": "Binary search?",
                "difficulty_score": 7,
                "difficulty_label": "HARD",
                "skill_tags": ["ALGORITHM"],
                "roles": {"primary": "DS"},
                "answers": {"detailed": "Divide the sorted search space."},
            },
        ]
        vector = np.full(len(COMPETENCY_KEYS), 8.0)
        vector[COMPETENCY_KEYS.index("sql")] = 2.0

        result = recommend_questions(vector, questions, num_recommendations=1)

        assert result[0]["question_id"] == "DB_001"
        assert result[0]["recommended_competency"] == "sql"
        assert result[0]["target_difficulty"] == "EASY"
        assert result[0]["recommendation_score"] > 0

    def test_adaptive_difficulty(self):
        assert adaptive_difficulty(2.5) == "easy"
        assert adaptive_difficulty(5.0) == "medium"
        assert adaptive_difficulty(7.5) == "hard"
        assert adaptive_difficulty(6.5, streak=3) == "hard"
        assert adaptive_difficulty(4.5, streak=-2) == "easy"


class TestGrader:
    def test_grade_answer_uses_local_fallback(self):
        result = grade_answer(
            question="What is a SQL join?",
            expected_answer="A SQL join combines rows from two tables using a related column.",
            candidate_answer="A join combines two tables by matching a related column.",
            scoring_rubric="Mentions combining tables and related columns.",
        )

        assert 0 <= result["score"] <= 10
        assert result["score"] > 3
        assert result["feedback"]
        assert isinstance(result["strengths"], list)
        assert isinstance(result["improvements"], list)

    def test_generate_follow_up_fallback(self):
        follow_up = generate_follow_up("Explain SQL join", "It combines tables.", "hard")

        assert isinstance(follow_up, str)
        assert "?" in follow_up
