# AI SQL Assistant (Task 1)

Upload any CSV/Excel dataset, get its schema auto-detected and loaded into a
dynamically created PostgreSQL table, then query it with natural language —
converted to SQL by Claude, validated by a strict allow-list/deny-list
parser, and executed through a database role that can only `SELECT`.

**Stack:** FastAPI (async) · pandas (ingestion) · sqlglot (SQL validation) ·
Anthropic Claude (NL→SQL + insights) · PostgreSQL 16 · Angular 19 · Docker.

## Why this is safe to point at arbitrary user data

The natural-language-to-SQL pattern has an obvious failure mode: what stops
the model (or a crafted prompt inside the CSV data itself) from generating
`DROP TABLE` or reading a different tenant's data? Three independent layers:

1. **`app/ai/sql_validator.py`** parses every generated query with `sqlglot`
   and rejects anything that isn't a single `SELECT`/CTE statement, or that
   references a table outside the one dataset it's scoped to, or calls a
   denylisted function (`pg_sleep`, `pg_read_file`, etc.). 20 unit tests
   cover this, including statement-stacking and cross-table-read attempts.
2. **A dedicated read-only Postgres role** (`sqlassistant_readonly`) executes
   the validated SQL — it has `SELECT`-only grants on the `datasets` schema
   and explicitly zero privileges on `public` (where app metadata lives). A
   bug in the validator still can't write data or read metadata tables.
3. **Identifiers are never derived from user input.** Uploaded column/table
   names are sanitized to `[a-z0-9_]` (or replaced with `col_N`) before ever
   appearing in a `CREATE TABLE`/`INSERT` statement — 10 unit tests cover
   this against SQL-injection-style headers.

Full writeup: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Local development (Docker — recommended)

```bash
cd task2-ai-sql-assistant
cp backend/.env.example backend/.env    
docker compose -f ../docker-compose.yml up --build sqlassistant-db sqlassistant-backend sqlassistant-frontend
```
(or just `docker compose up --build` from the repo root to start both tasks.)

- Backend: http://localhost:8001 (Swagger docs at `/api/docs`)
- Frontend: http://localhost:4201

## Local development (without Docker)

```bash
cd task2-ai-sql-assistant/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DB credentials + OPEN_API_KEY
alembic upgrade head   # creates metadata tables AND provisions the readonly role
uvicorn app.main:app --reload --port 8001
```
```bash
cd task2-ai-sql-assistant/frontend
npm install
npm start   # http://localhost:4201
```

**Try it with the included sample dataset** (`sample_data/sales_data.csv` —
308 rows with intentionally injected duplicates and missing values so every
example query in the assessment brief has something to find):
1. Upload it via the UI or `POST /api/v1/datasets/upload`.
2. Ask: *"Show top 10 customers by revenue"*, *"Find duplicate records"*,
   *"Which month generated the highest sales?"*, *"Show records with missing
   values"*, *"Generate a sales summary for the last quarter"*.

**Run tests** (30 tests, all pure/unit — no DB required):
```bash
cd task2-ai-sql-assistant/backend
PYTHONPATH=. pytest -v
```

## API documentation

Swagger UI: `/api/docs` · ReDoc: `/api/redoc`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/datasets/upload` | Upload CSV/Excel, auto-detect schema, create table |
| GET | `/api/v1/datasets` | List uploaded datasets |
| DELETE | `/api/v1/datasets/{id}` | Drop a dataset's table + metadata |
| POST | `/api/v1/datasets/{id}/query` | Ask a natural-language question, get validated SQL + results |
| GET | `/api/v1/datasets/{id}/history` | Query history for a dataset |
| GET | `/api/v1/datasets/{id}/insights` | AI-generated narrative insights (bonus) |
| POST | `/api/v1/datasets/{id}/export?format=xlsx\|csv\|pdf` | Re-run a question and export the result (bonus) |

## Deployment

Shares the same AWS VPS, host Nginx, and systemd/deploy.sh pattern as
Task 1 — see the repo root `README.md` and `deploy/` for the combined setup.
Production readonly-role provisioning uses `deploy/provision-readonly-role.sql`
with a real password, rather than the placeholder baked into the initial
migration for local dev convenience.
