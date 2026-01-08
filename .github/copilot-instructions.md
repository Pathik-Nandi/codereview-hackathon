<!-- Copilot instructions tailored to this repository. Keep <~50 lines. -->
# Copilot / AI assistant guidance for contributors

Purpose
- Help AI coding agents be immediately productive in this repo by summarizing architecture, workflows, and code patterns.

Quick architecture summary
- Backend: Flask app with multi-agent orchestration in `agents/` (see `agents/dispatcher.py` and `agents/main_agent.py`).
- Frontend: React + Vite in `frontend/` (entry: `frontend/src/main.jsx`).
- Persistence & RAG: PostgreSQL (models in `models/`) and Chroma/embedding logic under `services/rag_database_service.py` and `tools/clean_vector_db_and_rag.py`.

Key entrypoints & files
- Start backend: `main.py` — initializes services, agents, and API endpoints.
- Agents live in `agents/` and derive behavior from `agents/base_agent.py`.
- Database models and DTOs: `models/` (notably `models/analysis_result.py`, `models/database.py`).
- Service layer: `services/` (e.g., `services/github_service.py`, `services/database_service.py`).

Developer workflows (concrete commands)
- Install backend deps: `pip install -r requirements.txt`.
- Run backend (dev): `python main.py` (ensure `config/settings.yaml` and DB env vars are set).
- Run frontend (dev): from `frontend/`: `npm install` then `npm run dev`.
- Run tests: `pytest -q` (project has `pytest.ini` and `tests/`).

Project-specific patterns & conventions
- Agent pattern: implement an agent class in `agents/` and register/use it via `AgentDispatcher` / `main_agent`. See `agents/rag_enhanced_agent.py` for RAG examples.
- Services use small, focused classes in `services/` that accept DB or other service instances (dependency injection style).
- Models vs DTOs: persistable ORM models live in `models/database.py`; transient analysis outputs use `models/analysis_result.py`.
- Config: central YAML at `config/settings.yaml` and runtime flags via env vars read in `utils/config.py`.

Integration points & external dependencies
- GitHub integration: `services/github_service.py` — use for PR fetching, comments, and status updates.
- RAG / embeddings: `services/rag_database_service.py` and Chroma; see `tools/clean_vector_db_and_rag.py` for maintenance.
- Notifications: `services/slack_service.py`.

Where to add changes
- New agent: add `agents/<your_agent>.py`, subclass `BaseAgent` (`agents/base_agent.py`) and update `agents/dispatcher.py` or `agents/main_agent.py` to include it.
- New API endpoints: add routes in `main.py` (follow `@require_auth` usage for protected endpoints).

Testing & validation tips
- Unit tests live under `tests/`. Use fixtures in `tests/conftest.py` to create DB mocks and sample PR events.
- When changing persistence, update `documentation/create_tables.sql` and related migration steps.

Quick examples (copyable)
- Install deps and run backend:
```bash
pip install -r requirements.txt
python main.py
```
- Run tests:
```bash
pytest -q
```

If unsure
- Inspect `documentation/ARCHITECTURE.md` and `documentation/README.md` for high-level intent and design decisions.
- For agent orchestration specifics, read `agents/dispatcher.py` and `agents/main_agent.py`.

Please review and tell me which areas need more detail (e.g., DB migrations, environment setup, or CI commands).
