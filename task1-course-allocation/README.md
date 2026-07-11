# University Course Allocation System (Task 1)

AI-powered student course allocation system built for the Harvee Designs Full
Stack Developer assessment. Merit + reservation-aware allocation engine, a
live dashboard, and a natural-language analytics assistant backed by
tool-calling (not free-text SQL generation) for safety and auditability.

This is Task 1 of a two-task submission — see the
[repo root README](../README.md) for the combined overview, and
[Task 2 (AI SQL Assistant)](../task2-ai-sql-assistant/) for the other half.

**Stack:** FastAPI (async, SQLAlchemy 2.0) · Angular 19 (standalone components,
Tailwind) · PostgreSQL 16 · Claude (Anthropic API, tool use) · Docker Compose ·
GitHub Actions CI/CD · AWS VPS deployment.

## Project layout

```
task1-course-allocation/
├── backend/                 FastAPI application
│   ├── app/
│   │   ├── core/             config, DB session
│   │   ├── models/            SQLAlchemy models + enums
│   │   ├── schemas/          Pydantic request/response schemas
│   │   ├── services/          business logic (allocation engine, CRUD)
│   │   ├── ai/                AI assistant tool definitions + orchestration
│   │   └── api/v1/            FastAPI routers
│   ├── alembic/               DB migrations
│   ├── tests/                 pytest suite (allocation engine unit tests)
│   └── Dockerfile
├── frontend/                 Angular 19 application
│   ├── src/app/
│   │   ├── core/               models, API service, HTTP interceptor
│   │   ├── features/           dashboard, students, courses, allocation, ai-chat
│   │   └── shared/layout/      sidebar shell
│   └── Dockerfile              multi-stage: dev server / nginx production
├── sample_data/                seed script + ready-to-import CSVs (8 courses, 60 students)
└── docs/ARCHITECTURE.md        architecture, design decisions, security, challenges

Shared across both tasks, at the repo root (../):
├── docker-compose.yml / docker-compose.prod.yml   dev / prod stacks, both tasks
├── deploy/                                          deploy.sh, host Nginx configs, systemd unit
└── .github/workflows/                               task1-*-ci.yml, task2-*-ci.yml, deploy.yml
```

## Local development (Docker — recommended)

From the **repo root** (this starts both tasks; see root README to target only Task 1):
```bash
git clone <repo-url> && cd harvee-assessment
cp task1-course-allocation/backend/.env.example task1-course-allocation/backend/.env
# fill in ANTHROPIC_API_KEY at minimum
docker compose up --build task1-db task1-backend task1-frontend
```

- Backend: http://localhost:8000 (Swagger docs at `/api/docs`)
- Frontend: http://localhost:4200
- Postgres: localhost:5432

Migrations run automatically on backend container start (`alembic upgrade
head`, see `backend/Dockerfile`).

## Local development (without Docker)

**Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DB credentials + ANTHROPIC_API_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm start   # serves on http://localhost:4200, proxies API calls per environment.ts
```

**Load sample data** (60 students, 8 courses with reservation quotas):
```bash
cd backend
PYTHONPATH=. python ../sample_data/seed_sample_data.py
```
Or import the plain CSVs in `sample_data/csv/` through the API/UI if you'd
rather see the registration flow in action.

**Run tests:**
```bash
cd backend
PYTHONPATH=. pytest -v
```
The allocation algorithm (`app/services/allocation_engine.py`) is a pure
function with no DB dependency, so its 6 unit tests
(`tests/test_allocation_engine.py`) run in milliseconds and cover: merit
ordering, tie-breaking by application date, reservation quota enforcement,
non-conversion of unfilled reserved seats, preference fallback, and the
one-student-one-course invariant.

## API documentation

Interactive Swagger UI: `/api/docs` · ReDoc: `/api/redoc` · raw OpenAPI JSON:
`/api/openapi.json` — all auto-generated from the FastAPI route/schema
definitions, so they can never drift from the actual API surface.

Key endpoints:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/students` | Register a student with ranked course preferences |
| GET | `/api/v1/students` | List students (filter by category) |
| POST | `/api/v1/courses` | Create a course with per-category reserved seats |
| GET | `/api/v1/courses/{id}/stats` | Seats filled/available, category breakdown, rejection rate |
| POST | `/api/v1/allocation/run` | Execute the allocation algorithm (replaces prior results) |
| GET | `/api/v1/allocation/results` | Allocation outcome per student |
| GET | `/api/v1/dashboard/summary` | Aggregate stats for the dashboard |
| POST | `/api/v1/ai-assistant/ask` | Natural-language analytics Q&A |

## Deployment (AWS VPS)

See `docs/ARCHITECTURE.md` for the full picture. Short version: the shared
`../deploy/deploy.sh` pulls latest `main`, rebuilds Docker images for both
tasks, restarts the stack via the `harvee-assessment.service` systemd unit,
and health-checks both backends before declaring success.
`../.github/workflows/deploy.yml` runs it automatically over SSH after all
four CI workflows (both tasks' backend + frontend) pass on `main`.

## Architecture document

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for architecture design,
database design decisions, the AI integration approach, security
considerations, and challenges faced.
