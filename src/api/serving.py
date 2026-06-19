"""
serving.py — FastAPI backend bridge for InternHub.

Start from app.py:
    from src.api.serving import start_server
    start_server()

React calls http://localhost:8000/api/... (CORS open for localhost Streamlit).
"""

from __future__ import annotations
import sys
import threading
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_STATIC_DIR = _ROOT / "static"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False

try:
    import config as _cfg
    API_PORT: int = getattr(_cfg, "API_PORT", 8000)
except Exception:
    API_PORT = 8000

# ---------------------------------------------------------------------------
# Lazy src imports
# ---------------------------------------------------------------------------

def _grader():
    from src.ai import grader
    return grader

def _user_manager():
    from src.api import user_manager
    return user_manager

def _question_manager():
    from src.data import question_manager
    return question_manager

def _rec_engine():
    from src.kt import recommendation_engine
    return recommendation_engine

def _competency():
    from src.kt import competency_engine
    return competency_engine

# ---------------------------------------------------------------------------
# Key normalisation helpers
# React uses camelCase; all src/ functions expect snake_case.
# ---------------------------------------------------------------------------

def _normalize_question(q: dict) -> dict:
    """React camelCase question → Python snake_case for src/ functions."""
    if not q:
        return q
    n = dict(q)
    if "id" in n and "question_id" not in n:
        n["question_id"] = n["id"]
    if "questionType" in n and "question_type" not in n:
        n["question_type"] = n["questionType"]
    if "skillGroups" in n and "skill_groups" not in n:
        n["skill_groups"] = n["skillGroups"]
    if "tags" in n and "skill_tags" not in n:
        n["skill_tags"] = n["tags"]
    # role (flat string) → nested roles dict
    if "role" in n and "roles" not in n:
        n["roles"] = {"primary": n["role"]}
    # question text
    if "question_text" not in n:
        n["question_text"] = n.get("body_en") or n.get("title_en", "")
    # deterministic grader needs answers.correct_option_id
    if "correctOptionId" in n or "correctAnswer" in n or "acceptedAnswers" in n:
        answers = dict(n.get("answers", {}))
        if "correctOptionId" in n:
            answers.setdefault("correct_option_id", n["correctOptionId"])
        if "correctAnswer" in n:
            answers.setdefault("correct_answer", n["correctAnswer"])
        if "acceptedAnswers" in n:
            answers.setdefault("accepted_answers", n["acceptedAnswers"])
        if "explanation" in n:
            answers.setdefault("explanation", n["explanation"])
        if "options" in n:
            answers.setdefault("options", n["options"])
        n["answers"] = answers
    return n


def _normalize_candidate_response(cr: dict) -> dict:
    """React {answer, code} → Python {free_text, code}."""
    if not cr:
        return cr
    n = dict(cr)
    # grader.py reads "free_text"; React sends "answer"
    if "answer" in n and "free_text" not in n:
        n["free_text"] = n["answer"]
    return n


def _build_skill_vector_from_results(role: str, results: list[dict]) -> dict:
    """Build an initial skill vector by applying EMA updates from results list.
    Each item must have: {score (0-1 or 0-10), question (React format)}
    Falls back to init_skill_vector if questions are absent.
    """
    ce = _competency()
    sv = ce.init_skill_vector(role)
    for r in results:
        q_raw = r.get("question") or {}
        q = _normalize_question(q_raw)
        score = float(r.get("score", 0.0))
        # Normalise to 0-1 if score looks like 0-10 scale
        if score > 1.0:
            score = score / 10.0
        kc = ce.question_to_kc(q, role)
        sv = ce.update_skill_after_answer(sv, kc, score)
    return sv


# ---------------------------------------------------------------------------
# FastAPI app + CORS
# ---------------------------------------------------------------------------

if _FASTAPI_OK:
    app = FastAPI(title="InternHub API", version="1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request schemas ─────────────────────────────────────────────────────

    class GradeRequest(BaseModel):
        question: dict
        candidate_response: dict
        user_id: str | None = None

    class CreateUserRequest(BaseModel):
        user_id: str
        role: str

    class AnswerRequest(BaseModel):
        question: dict
        grade_result: dict

    class AssessmentStage1Request(BaseModel):
        role: str
        exclude_ids: list[str] = []

    class AssessmentFinalizeRequest(BaseModel):
        user_id: str
        role: str
        stage1_results: list[dict]
        stage2_results: list[dict]
        stage2_is_hard: bool

    # ── Endpoints ────────────────────────────────────────────────────────────

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "1.0"}

    @app.post("/api/grade")
    async def api_grade(req: GradeRequest):
        import sys
        qtype = req.question.get("questionType", req.question.get("question_type", "?"))
        print(f"[serving] /api/grade called — type={qtype}", file=sys.stderr, flush=True)
        try:
            question  = _normalize_question(req.question)
            candidate = _normalize_candidate_response(req.candidate_response)
            result    = _grader().grade_answer(question, candidate)
            print(f"[serving] /api/grade result — score={result.get('score')}, method={result.get('method')}", file=sys.stderr, flush=True)
            if req.user_id:
                try:
                    _user_manager().update_after_answer(req.user_id, question, result)
                except Exception:
                    pass
            return result
        except Exception as e:
            print(f"[serving] /api/grade ERROR: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/user/create")
    async def api_create_user(req: CreateUserRequest):
        try:
            profile = _user_manager().create_user_profile(req.user_id, req.role)
            return profile
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/user/{user_id}")
    async def api_get_user(user_id: str):
        profile = _user_manager().get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        return profile

    @app.get("/api/user/{user_id}/summary")
    async def api_user_summary(user_id: str):
        summary = _user_manager().get_user_summary(user_id)
        if not summary:
            raise HTTPException(status_code=404, detail="User not found")
        return summary

    @app.post("/api/user/{user_id}/answer")
    async def api_record_answer(user_id: str, req: AnswerRequest):
        try:
            question = _normalize_question(req.question)
            updated  = _user_manager().update_after_answer(
                user_id, question, req.grade_result
            )
            return updated
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/recommend/{user_id}")
    async def api_recommend(user_id: str, n: int = 5):
        profile = _user_manager().get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            questions = _rec_engine().get_next_questions(profile, n=n)
            return {"questions": questions}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/assessment/stage1")
    async def api_stage1(req: AssessmentStage1Request):
        try:
            questions = _question_manager().generate_stage1(
                req.role, set(req.exclude_ids)
            )
            return {"questions": questions}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/assessment/finalize")
    async def api_finalize(req: AssessmentFinalizeRequest):
        try:
            result = _question_manager().finalize_assessment(
                req.role,
                req.stage1_results,
                req.stage2_results,
                req.stage2_is_hard,
            )
            if req.user_id:
                try:
                    # Build skill vector from assessment results to pass to update_from_assessment
                    all_results = [*req.stage1_results, *req.stage2_results]
                    sv = _build_skill_vector_from_results(req.role, all_results)
                    _user_manager().update_from_assessment(
                        req.user_id,
                        req.role,
                        float(result["stage1_score"]),
                        float(result["stage2_score"]),
                        req.stage2_is_hard,
                        sv,
                    )
                except Exception:
                    pass
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# Serve static UI files — uvicorn sets correct MIME types (Streamlit does not)
# ---------------------------------------------------------------------------

if _FASTAPI_OK:
    try:
        from fastapi.staticfiles import StaticFiles
        _STATIC_DIR.mkdir(parents=True, exist_ok=True)
        app.mount("/ui", StaticFiles(directory=str(_STATIC_DIR), html=True), name="ui")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Background-thread launcher
# ---------------------------------------------------------------------------

_server_started = False
_lock = threading.Lock()


def start_server(port: int = API_PORT, log_level: str = "warning") -> bool:
    """Start FastAPI in a daemon thread. Safe to call multiple times."""
    global _server_started
    if not _FASTAPI_OK:
        return False
    with _lock:
        if _server_started:
            return True
        t = threading.Thread(
            target=uvicorn.run,
            kwargs={
                "app": app,
                "host": "0.0.0.0",
                "port": port,
                "log_level": log_level,
            },
            daemon=True,
            name="internhub-api",
        )
        t.start()
        _server_started = True
        return True
