# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install deps
pip install -r requirements.txt

# Run the main app (Streamlit shell + FastAPI bridge + React frontend)
streamlit run app.py

# Run tests
pytest tests/ -v
pytest tests/test_core.py -v                          # single file
pytest tests/test_core.py::TestCompetencyEngine -v     # single class
pytest tests/test_core.py::TestCompetencyEngine::test_create_competency_vector -v  # single test
```

There is no JS build step for the main app's frontend — JSX files in `app/frontend/` are transpiled in-browser by Babel standalone (no npm/webpack). Edits there take effect on next Streamlit rerun; `app.py`'s `prepare_static()` only re-copies a file into `static/` if its source mtime changed.

### `it-rcmsys-app/` (separate Vercel deployment)

This is a self-contained second copy of the app, deployed independently to Vercel (its own git remote, `github.com/ZaKhimNe/interview-it-recsys-app`, **not** a subtree of the main repo's git history). It has its own `requirements.txt`, `src/` (trimmed copy of `src/ai`, `src/data`, `src/kt`), and `public/` (JSX frontend, structurally similar to `app/frontend/` but with a different MST flow — 7 placement + 3 adaptive questions vs. the main app's 4+6 — and its own KT-model demo screen). Treat the two frontends as forks, not the same source of truth — a fix in one does not automatically apply to the other.

- `vercel.json`: `"framework": null` is required (Vercel otherwise misdetects the `requirements.txt` + Python `buildCommand` combo as a single-entrypoint web app instead of per-file `/api` serverless functions). Do **not** add a `functions` block unless every entry has at least one non-empty property and a valid versioned runtime string — Vercel auto-infers the Python runtime for everything under `/api` from the root `requirements.txt` already, so the simplest config (no `functions` key at all) is the most reliable.
- `build.py` only regenerates `public/index.html`; static assets and JSX are committed directly.
- Push with `git push origin main` from inside `it-rcmsys-app/` — it is a separate repo rooted in that subfolder.

## Architecture

### Three layers, two transport formats

1. **Data layer** (`src/data/`, `data/`) — `data_loader.py` loads and normalizes `data/raw/question_bank/question_bank.json` (~2122 questions) into a canonical Python schema (snake_case: `question_id`, `skill_groups`, `roles.primary`, etc.). `data/schemas/` holds JSON Schemas for the question bank, skill taxonomy, JD requirements, and user profile.
2. **KT / scoring layer** (`src/kt/`, `kt_models/`) — see below.
3. **Serving layer** (`src/api/serving.py`, `app.py`) — bridges Python data/KT to the React frontend.

The Python backend and React frontend speak different naming conventions (snake_case vs. camelCase) and different question schemas (`skill_groups` vs `skillGroups`, `question_id` vs `id`). Normalization happens at the boundary in two places: `app.py`'s `_map_question()` (Python → React, used when building `window.__INTERNHUB_DATA__`) and `src/api/serving.py`'s `_normalize_question()` / `_normalize_candidate_response()` (React → Python, used by the `/api/*` FastAPI endpoints). When adding a question field, it usually needs to be threaded through both directions.

### Main app serving stack (`app.py`)

Streamlit can't serve static files with correct MIME types (it returns `text/plain` for `.html`, which browsers refuse to render), so the actual UI is **not** served by Streamlit. Instead:

1. `app.py` starts a FastAPI server in a background thread (`src/api/serving.py:start_server()`, port from `config.API_PORT`, default 8000).
2. FastAPI mounts `static/` at `/ui` via `StaticFiles(html=True)` — uvicorn sets correct content types.
3. `app.py` writes `app/frontend/*.jsx` + a generated `index.html` (with `window.__INTERNHUB_DATA__` containing the full question bank, skill axes, and role targets serialized from Python) into `static/`.
4. The Streamlit page is just an `<iframe src="http://localhost:8000/ui/index.html">`.
5. The React frontend calls back into `/api/...` (grading, user profile, assessment finalize) via `fetch`.

### Frontend (`app/frontend/*.jsx`, no bundler)

Plain `<script type="text/babel" src="...">` tags loaded in a fixed order (`state.jsx → chrome.jsx → widgets.jsx → screens-*.jsx → router.jsx`, see `JSX_ORDER` in `app.py`). These are **not ES modules** — every file shares one global scope, so `const`/`function` declared in an earlier-loaded file is visible in a later one without imports. `state.jsx` defines the global store (`StoreProvider`/`useStore`, React Context + `sessionStorage`), mock/fallback data (`QUESTIONS`, `SKILL_AXES`, `SKILL_KEYS`, `ROLE_TARGETS`), and overrides those constants in-place from `window.__INTERNHUB_DATA__` if present. Because there's no bundler, a syntax error or truncated file anywhere in the chain throws once at parse time and silently kills the entire app (blank page, nothing in `#root}`) — there is no per-file isolation.

The diagnostic flow (Multi-Stage Testing / MST) lives in `screens-diagnostic.jsx`: Stage 1 (placement questions) → routing decision (WEAK/MID/STRONG by average score) → Stage 2 (adaptive questions, prioritized by weak skill groups from Stage 1) → a per-axis skill vector update. Vector deltas are computed **per skill axis** by matching each question's `skillGroups` against the role's `SKILL_KEYS` (machine-readable keys parallel to the human-readable `SKILL_AXES` labels) — untested axes are left unchanged, and a first-ever assessment maps raw score directly to `score × target` per axis rather than starting from 0 and applying an incremental delta (a delta against a 0 baseline can't produce a meaningful first reading).

### Knowledge Tracing (`kt_models/`, `src/kt/`)

Three interaction-sequence models — `BKT` (Bayesian, per-KC 4-param), `DKT` (LSTM), `SAKT` (self-attention) — trained offline via the `notebooks/01_eda → 02_feature_engineering → 03_train_models → 04_evaluation` pipeline against `data/processed/{train,val,test}_seqs.pkl`, with fitted weights saved to `results/models/`. At runtime, `src/kt/kt_predictor.py` loads the best model (`dkt_quality` by default) and predicts a 0.05–0.99 mastery estimate per KC, falling back to `{}` (caller uses EMA-only) if the model can't load or history is too short (`_MIN_HISTORY = 3`).

The skill vector update pipeline (used in `src/api/user_manager.py`, mirrored in `it-rcmsys-app/public/screens-progress.jsx`'s demo) always runs an EMA update first, then blends in the KT prediction once enough history exists: **KT(70%) + EMA(30%)**. This 70/30 blend is a deliberately consistent constant across the Python backend and both frontends — don't special-case one without the other.

### Knowledge Component (KC) taxonomy

17 KCs across 3 roles, defined once in `config.py:KC_BY_ROLE` (DA: 5, DS: 7, DE: 5) and re-derived/duplicated in `src/kt/competency_engine.py:ROLE_COMPETENCIES` and `SKILL_GROUP_TO_KC` (a many-to-one map from granular question tags like `SQL_WINDOW_FUNCTION` down to the 17 canonical KCs). Questions are tagged with `skill_groups` at the granular level; `SKILL_GROUP_TO_KC` is the lookup used to roll them up to a KC for scoring/KT purposes.

### Grading (`src/ai/grader.py`)

Free-text/code answers are graded by Gemini (`config.LLM_MODEL_NAME`) with a deterministic local-rubric fallback (`_local_grade`, 4-layer weighted score: keyword/concept match 50%, ... 10%) used both as a backup when the Gemini call raises, and directly for objective question types (MC/True-False/Fill-blank) which are scored client-side without an LLM call at all. When Gemini fails, the raw exception is surfaced in the response as `gemini_error` so failures are visible in DevTools Network rather than only server logs.
