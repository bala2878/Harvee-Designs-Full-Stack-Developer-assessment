# Harvee Designs — Full Stack Developer Assessment

Submission by Balakrishnan D. Both tasks, one repo, shared CI/CD and
deployment pattern. Each task is fully self-contained with its own backend,
frontend, tests, and architecture document — start with whichever interests
you first.

## Contents

| | |
|---|---|
| [`task1-course-allocation/`](task1-course-allocation/) | **Task 1** — AI-powered student course allocation system. Merit + reservation-aware allocation engine, live dashboard, Claude-powered analytics assistant (fixed tool-use). |
| [`task2-ai-sql-assistant/`](task2-ai-sql-assistant/) | **Task 2** — Upload any CSV/Excel, query it in natural language. Claude-generated SQL validated by a custom parser and executed through a read-only DB role. |

Each has its own `README.md` (setup instructions) and `docs/ARCHITECTURE.md`
(the required architecture document — design decisions, AI integration
approach, security considerations, challenges faced).

## Quick start — run everything locally

```bash
git clone <repo-url> && cd harvee-assessment
cp task1-course-allocation/backend/.env.example task1-course-allocation/backend/.env
cp task2-ai-sql-assistant/backend/.env.example task2-ai-sql-assistant/backend/.env
# edit both .env files: at minimum, set ANTHROPIC_API_KEY in each

docker compose up --build
```

- Task 1 — Allocation dashboard: http://localhost:4200 (API: :8000, docs at `/api/docs`)
- Task 2 — SQL Assistant: http://localhost:4201 (API: :8001, docs at `/api/docs`)

Each task also runs standalone without Docker — see the per-task READMEs.

## What to look at first, if short on time

1. **`task1-course-allocation/backend/app/services/allocation_engine.py`** +
   its test file — the allocation algorithm as a pure, DB-free function, with
   6 tests covering every stated business rule including an explicitly
   documented policy decision (unfilled reserved seats don't auto-convert
   within a round).
2. **`task2-ai-sql-assistant/backend/app/ai/sql_validator.py`** + its test
   file — the safety boundary between AI-generated SQL and execution, with
   20 tests including real injection patterns (statement stacking,
   cross-table reads, denylisted functions).
3. Both tasks' `docs/ARCHITECTURE.md` — written to explain *why*, not just
   *what*, including gaps deliberately left out of scope (no auth, no
   AI-assistant rate limiting) rather than leaving them unaddressed.

## Testing

```bash
cd task1-course-allocation/backend && PYTHONPATH=. pytest -v   # 6 tests, allocation engine
cd task2-ai-sql-assistant/backend && PYTHONPATH=. pytest -v    # 30 tests, SQL validator + ingestion
```
All 36 tests are pure unit tests — no database or network dependency, so
they run in well under a second total and can't flake in CI on
infrastructure issues.

## CI/CD and deployment

- `.github/workflows/task{1,2}-{backend,frontend}-ci.yml` — lint + test on
  every push/PR, path-filtered so a Task 1 change doesn't trigger Task 2's
  pipeline and vice versa.
- `.github/workflows/deploy.yml` — deploys to a AWS VPS over SSH after
  CI passes on `main`, running `deploy/deploy.sh`.
- `deploy/` — host Nginx configs (one per task, two subdomains), a single
  systemd unit wrapping `docker compose` for both stacks, and the deploy
  script itself (build, restart, health-check both backends, provision
  Task 2's read-only DB role).
- `docker-compose.yml` (dev) / `docker-compose.prod.yml` (VPS) — both tasks
  run as independent service groups sharing one Docker network setup; see
  the comments at the top of `docker-compose.prod.yml` for why per-task
  environment variables are namespaced (`TASK1_*` / `TASK2_*`) rather than
  shared.

## Stack

FastAPI (async, SQLAlchemy 2.0) · Angular 19 (standalone components,
Tailwind) · PostgreSQL 16 · Claude (Anthropic API — tool-use in Task 1,
NL-to-SQL + insights in Task 2) · Docker Compose · GitHub Actions ·
AWS VPS.
