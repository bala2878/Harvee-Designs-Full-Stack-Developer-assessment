# Architecture Document — University Course Allocation System

## 1. Architecture Design

```
┌─────────────┐      HTTPS       ┌──────────────────┐
│   Browser   │ ───────────────► │  Host Nginx (VPS) │  TLS termination, gzip
└─────────────┘                  └────────┬──────────┘
                                           │ proxy_pass :8080
                                  ┌────────▼──────────┐
                                  │ frontend container │  Angular SPA (static) +
                                  │  (nginx:alpine)    │  nginx proxies /api/ ──┐
                                  └─────────────────────┘                       │
                                                                                 ▼
                                                                    ┌────────────────────┐
                                                                    │  backend container  │
                                                                    │  FastAPI + uvicorn   │
                                                                    │  (4 workers)          │
                                                                    └──────────┬───────────┘
                                                                               │ asyncpg
                                                                    ┌──────────▼───────────┐
                                                                    │   db container         │
                                                                    │   PostgreSQL 16         │
                                                                    └────────────────────────┘
                                                                               ▲
                                                                               │ tool-use results
                                                                    ┌──────────┴───────────┐
                                                                    │  Chatgpt API  │
                                                                    │  (AI assistant)         │
                                                                    └────────────────────────┘
```

Three containers (`db`, `backend`, `frontend`) run on a single AWS VPS
under Docker Compose, wrapped by a systemd unit for auto-restart on boot/crash.
Host-level Nginx terminates TLS and reverse-proxies to the frontend container;
the frontend's own internal Nginx serves the compiled Angular bundle and
proxies `/api/*` to the backend over the Docker-internal network, so the
backend is never directly exposed to the internet. This two-hop proxy (host
Nginx → container Nginx → uvicorn) keeps certificate renewal (`certbot`) 
entirely a host-level concern — rotating TLS certs never requires touching a
container image.

**Why a monorepo, single-VPS deployment rather than split services /
Kubernetes:** the assessment's scope (one allocation engine, one dashboard)
doesn't justify the operational overhead of a container orchestrator. A
docker-compose + systemd + Nginx stack is the same pattern used in production
for the author's other SaaS projects at this scale, and it's trivial to
graduate to managed Postgres / a container platform later without changing
any application code — the split into `db` / `backend` / `frontend` services
already mirrors how those would be separated.

## 2. Database Design Decisions

- **Normalized to 3NF.** `students`, `courses`, `course_seat_reservations`,
  `course_preferences`, `allocations`, and `allocation_runs` are separate
  tables rather than, say, storing preferences as a JSON array on `students`.
  This makes preference-level queries (e.g. "who ranked Course X as their 1st
  choice") a plain indexed join instead of a JSON-array scan, and lets the AI
  assistant's tools stay simple SQL rather than JSON-path expressions.
- **`course_seat_reservations` is its own table, not fixed columns on
  `courses`** (e.g. `obc_seats`, `sc_seats`, `st_seats`). Reservation
  categories vary by jurisdiction/policy and the brief only fixes
  OBC/SC/ST/GENERAL for *this* assessment — a separate
  `(course_id, category, reserved_seats)` table means adding a new
  reservation category is a data change, not a schema migration.
- **`allocation_runs` as an audit trail.** Every time the allocation
  algorithm executes, it creates an `AllocationRun` row and stamps every
  resulting `Allocation` with that run's ID. Re-running the algorithm
  replaces the `allocations` table's contents but keeps the run history —
  this was a deliberate choice so "why did student X get a different result
  this time" is always answerable (which run produced it, when, and the
  aggregate counts at that time), instead of allocations silently
  overwriting with no trace.
- **`Allocation.course_id` is nullable with `status` as an explicit enum**
  (`ALLOCATED` / `NOT_ALLOCATED`) rather than just leaving a `NULL` row absent
  for unallocated students. A student who applied but got nothing is a
  first-class fact the dashboard and AI assistant need to report on, not an
  absence to infer.
- **One `allocations` row per student, enforced by a unique constraint on
  `student_id`** — encodes business rule #4 ("a student can be allocated only
  one course") at the database level, not just in application code.
- **Postgres native ENUM types** (`category_enum`, `allocation_status_enum`,
  `allocation_run_status_enum`) instead of plain strings or a lookup table —
  gives Postgres-level validation with zero extra joins, at the cost of a
  migration to add a new enum value (acceptable given these categories are
  policy-defined, not user-editable data).
- **Composite index on `(marks DESC, application_date ASC)`** on `students`
  mirrors the exact sort order the allocation algorithm uses for global merit
  ranking, so the ORDER BY the algorithm relies on is index-backed rather than
  a full table sort once student counts grow into the thousands.

## 3. AI Integration Approach

Two distinct AI surfaces exist across both tasks, and both follow the same
underlying philosophy: **the LLM is a natural-language front-end over a
constrained, auditable execution layer — never a free-form code/SQL
generator with direct database access.**

**Task 1 (this document): fixed-tool analytics assistant.** The user's
question goes to Claude with a small set of ~5 read-only tool definitions
(`get_allocation_count_per_course`, `get_students_without_first_preference`,
`get_course_rejection_rates`, `get_category_wise_allocation_summary`,
`get_unallocated_students` — see `backend/app/ai/tools.py`). Claude decides
which tool(s) the question needs, the backend executes the corresponding
parameterized SQLAlchemy query, the result is fed back to Claude as a
`tool_result`, and Claude composes the final natural-language answer strictly
from that data (system prompt explicitly forbids inventing numbers). A bounded
loop (`MAX_TOOL_ROUNDS = 4`) prevents runaway tool-calling. This means:

- The model can never run arbitrary SQL against production data.
- Every tool call and its result is logged and returned to the frontend
  (`tool_calls` in the response), so "why did the assistant say that" is
  always inspectable — this is what the "Tools used: ..." footer under each
  assistant message in the UI is for.
- Adding a new answerable question is a matter of writing one more small,
  reviewable function — not expanding what the model is trusted to execute.

**Task 2 will use the same posture with one necessary difference:** since its
entire purpose is querying *arbitrary uploaded datasets* (schema unknown in
advance), a fixed tool set isn't possible. There, natural language is
converted to a single `SELECT`-only query, which is then parsed and validated
(table/column allow-list derived from the uploaded dataset's own detected
schema, statement type restricted to `SELECT`, row limit enforced) before
execution — full details in Task 2's own architecture section once that
submission is prepared.

**Model:** `claude-sonnet-4-6` via the official `anthropic` Python SDK
(async client). Provider is abstracted behind `AI_PROVIDER` in config for a
future OpenAI/Gemini swap without touching call sites, though only the
Anthropic path is implemented for this submission.

## 4. Security Considerations

- **No arbitrary SQL/code execution surface for the LLM** (see §3) — the
  single biggest AI-specific risk in either task.
- **Input validation at the schema layer.** Pydantic validators reject
  malformed preference lists (non-sequential priorities, duplicate courses),
  out-of-range marks, and reservation totals that exceed a course's total
  seats — before any of it reaches the database.
- **Parameterized queries throughout.** SQLAlchemy's query builder is used
  exclusively; no raw string interpolation into SQL anywhere in the codebase.
- **CORS is allow-listed** (`BACKEND_CORS_ORIGINS`), not wildcarded, and is
  environment-driven so production only trusts the actual deployed frontend
  origin.
- **Secrets never committed.** `.env` / `.env.prod` are git-ignored; only
  `.env.example` (no real values) is committed. Production secrets live in
  `.env.prod` on the VPS, referenced by `docker-compose.prod.yml` via
  `env_file`, and are injected into GitHub Actions as encrypted repository
  secrets for the SSH deploy step.
- **Least-network-exposure by design.** Only the host Nginx (ports 80/443)
  and SSH are reachable from the internet; Postgres and the backend container
  are only reachable on the Docker-internal network (`internal` network in
  `docker-compose.prod.yml` has no published ports).
- **Non-root container users.** The backend Dockerfile creates and switches
  to an unprivileged `appuser` before running the application.
- **Structured error handling.** A global FastAPI exception handler returns a
  generic `500` to clients while logging the full traceback server-side —
  stack traces and internal details are never leaked in API responses.
- **Rate-limit hook for the AI assistant** (`AI_ASSISTANT_RATE_LIMIT_PER_MIN`
  in config) is defined and ready to wire into a dependency — noted here as a
  known gap: not yet enforced in this submission (see Challenges below).

**Not implemented in this submission, called out explicitly rather than
silently skipped:** authentication/authorization (JWT scaffolding exists in
config — `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — but no
login endpoint or route guards were built, since the brief's business rules
describe a single-operator counselling workflow with no stated multi-role
requirement). In a real deployment this would be the first addition: staff
login for course/allocation management, no auth needed for a
read-only public results lookup if that's ever required.

## 5. Challenges Faced and Solutions Implemented

- **Reservation-vs-general seat interaction.** The trickiest allocation-logic
  decision was what happens to a category's *unfilled* reserved seats within
  a single round — do they convert to general seats and get taken by a
  higher-merit general-category student, or stay reserved and go empty?
  This assessment's algorithm keeps them reserved for that round (documented
  explicitly in `test_unfilled_reserved_seats_do_not_block_general_students`
  and in the algorithm's own docstring) rather than silently guessing — real
  counselling systems vary on this by policy, and the test exists specifically
  so the behavior is a stated, verifiable decision rather than an accident of
  the implementation.
- **Postgres ENUM + Alembic `DuplicateObject` errors.** Reusing the same
  Postgres enum type (e.g. `category_enum`) across two tables
  (`students.category` and `course_seat_reservations.category`) causes
  Alembic's naive autogenerate to try `CREATE TYPE category_enum` twice,
  which fails on the second table. Fixed by creating each enum type exactly
  once at the top of the migration (`category_enum.create(bind,
  checkfirst=True)`) and declaring every column that uses it with
  `create_type=False`, so SQLAlchemy never re-issues the `CREATE TYPE`
  statement.
- **Keeping the allocation algorithm testable without a database.** Early on,
  allocation logic was tangled together with SQLAlchemy session code, which
  made it slow and awkward to unit test edge cases (tie-breaking, quota
  exhaustion). Refactored into `allocation_engine.py` (pure functions,
  dataclass inputs/outputs, zero DB imports) with a separate
  `allocation_orchestrator.py` that only handles loading from / persisting to
  the database. This let the 6 core algorithm tests run in ~30ms with no
  Postgres dependency, and CI runs them even when the DB service container is
  slow to become healthy.
- **AI assistant rate limiting is designed but not enforced.** Configuration
  for it exists (`AI_ASSISTANT_RATE_LIMIT_PER_MIN`), but wiring it into a
  FastAPI dependency (in-memory token bucket, or Redis if the assistant
  becomes multi-instance) was deprioritized in favor of finishing Task 2
  within the assessment window — flagged here rather than left as a silent
  gap, since an unbounded `/ai-assistant/ask` endpoint is the one
  cost/abuse-relevant surface in this submission that isn't yet protected
  beyond normal Anthropic API usage limits.
