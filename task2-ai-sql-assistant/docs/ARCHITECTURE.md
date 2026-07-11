# Architecture Document — AI SQL Assistant

## 1. Architecture Design

```
Browser ─▶ frontend (nginx + Angular SPA) ─▶ /api/ ─▶ backend (FastAPI, uvicorn, port 8001)
                                                            │
                                          ┌─────────────────┼──────────────────┐
                                          ▼                                    ▼
                              main DB session (DDL-capable)        readonly DB session
                              creates/drops dataset tables,        (sqlassistant_readonly role,
                              writes metadata + history             SELECT-only on `datasets` schema)
                                          │                                    │
                                          └───────────────┬────────────────────┘
                                                           ▼
                                                  PostgreSQL 16
                                                  ├─ public schema: datasets, query_history (metadata)
                                                  └─ datasets schema: ds_<uuid> (one table per upload)

                                          Anthropic Claude API
                                          ├─ NL question + schema → generated SQL (app/ai/nl_to_sql.py)
                                          └─ schema + stats → narrative insights (app/ai/insights.py)
```

**Two SQLAlchemy engines, deliberately.** `app/core/db.py` maintains a main
async engine (the application's own DB user — can `CREATE`/`DROP` tables,
used for ingestion and metadata writes) and a **separate** read-only engine
connected as `sqlassistant_readonly`, used for exactly one thing: executing
AI-generated SQL. This split is the architecture's central security
decision — see §4.

**Why dynamic per-upload tables rather than one big "generic data" table
with a JSONB blob column:** a real Postgres table with real typed columns
means (a) the AI-generated SQL can use normal `WHERE revenue > 100` /
`GROUP BY category` semantics instead of JSONB path operators the model is
more likely to get wrong, (b) Postgres can use real indexes and type
checking, and (c) `EXPLAIN`-level query performance is what a user would get
querying their own database directly, not a JSON-in-a-column workaround.

## 2. Database Design Decisions

- **Metadata (`datasets`, `query_history`) lives in `public`; uploaded data
  lives in a separate `datasets` schema.** This isn't just tidiness — it's
  what makes the read-only role's privilege grant a single, simple statement
  (`GRANT SELECT ON ALL TABLES IN SCHEMA datasets`) instead of a
  table-by-table allow-list that has to be updated on every upload.
- **`Dataset.columns_metadata` is JSONB, not a separate `dataset_columns`
  table.** Column metadata (original name, sanitized name, inferred type) is
  read as a whole every time it's needed (building the AI prompt, rendering
  the frontend's column list) and never queried by individual column — a
  normalized child table would only add join overhead for zero query
  benefit here, unlike Task 1's `course_preferences`, which genuinely is
  queried preference-by-preference.
- **`query_history` logs failures, not just successes.** `success: bool` +
  `error_message` are recorded even when SQL generation or execution fails.
  This was a deliberate choice so the history tab (and, if ever needed, a
  "why do my queries keep failing" debugging session) has the full picture —
  logging only successful queries would hide exactly the cases worth
  investigating.
- **Table names are `ds_<12 hex chars>`, generated server-side, never from
  the uploaded filename.** Two people uploading files both named
  `data.csv` on the same day must not collide, and — more importantly — the
  physical table name must never be influenced by anything in the upload,
  since it becomes part of every subsequent `SELECT ... FROM` statement (see
  §4 and `app/services/dataset_service.py`'s module docstring for the full
  reasoning).

## 3. AI Integration Approach

Two AI calls, both scoped as narrowly as the task allows:

**NL → SQL (`app/ai/nl_to_sql.py`).** Claude receives the dataset's schema
(sanitized column names + inferred Postgres types) and the user's question,
with a system prompt that pins it to exactly one table and forbids anything
but a single `SELECT`. Critically, **the model's output is a hint, not a
grant of trust** — every generated query is re-parsed and independently
validated (`app/ai/sql_validator.py`) before touching the database, so even
if the model were tricked (e.g. by adversarial content embedded in the
question, or a future prompt-injection technique) into emitting a
destructive statement, that statement is structurally incapable of executing
— it would fail the single-statement check, the SELECT-only check, or the
table allow-list, independent of what the model "believed" it was doing.

**AI-generated insights (`app/ai/insights.py`, bonus).** Rather than handing
the model raw rows (which risks quoting large slices of potentially
sensitive uploaded data back in a response, and blows up token usage on
large datasets), the backend pre-computes lightweight aggregate stats
(row count, per-column null counts) and asks the model to synthesize a
short narrative from those numbers. The model never sees row-level data for
this feature.

**Same posture as Task 1, one necessary difference.** Task 1's AI assistant
uses a fixed set of ~5 hand-written tools because its question space is
narrow and known in advance. Task 2's entire premise — arbitrary uploaded
datasets with unknown schemas — makes a fixed tool set impossible; natural
language must become a genuinely dynamic query. That's exactly why Task 2
needs the heavier validation layer Task 1 doesn't: Task 1 never lets the
model produce SQL at all, so there's nothing to validate; Task 2's validator
is what recreates an equivalent safety guarantee for a task where fixed
tools aren't an option.

**Model:** `claude-sonnet-4-6` via the async `anthropic` SDK, same as Task 1.

## 4. Security Considerations

This is the task where AI-specific security is the central design problem,
not an add-on. In order of how much of the risk each one closes:

1. **Defense in depth, not a single gate.** Four independent checks in the
   validator (single statement / SELECT-only / table allow-list /
   denylisted functions) plus a database-level read-only role means a
   failure in any *one* layer doesn't equal a breach — the SQL still has to
   get past the ones that remain, and worst case, past what the database
   role is physically capable of doing.
2. **Table allow-list is the load-bearing check.** Even a "successful"
   prompt-injection that gets the model to emit a syntactically valid
   `SELECT * FROM public.datasets` (trying to read *other users'* dataset
   metadata) is rejected — the validator only accepts the one table this
   query was scoped to, and the `sqlassistant_readonly` role has zero grants
   on `public` regardless.
3. **No identifier ever originates from user input** (see §2/§4 dataset
   service docstring) — the class of injection where a malicious *column
   name* (not just query text) becomes part of executable SQL is closed
   structurally, not by escaping.
4. **`SET LOCAL statement_timeout`** on every query execution — a query that
   passes validation but is still expensive (e.g. an intentionally
   inefficient join within the single allowed table) can't hang a
   connection indefinitely.
5. **Upload limits** (`MAX_UPLOAD_SIZE_MB`, `MAX_UPLOAD_ROWS`) bound the
   worst case for both ingestion time and the size of what the read-only
   role is scanning per query.
6. **Row limit is enforced by the validator, not requested of the model.**
   Every query gets a `LIMIT` injected or clamped server-side
   (`MAX_RESULT_ROWS`) regardless of what the generated SQL asked for —
   the model cannot accidentally (or deliberately) return the model's
   sense of "everything."
7. **Secrets, CORS, non-root containers, generic error responses** — same
   posture as Task 1, not repeated in full here; see Task 1's
   `docs/ARCHITECTURE.md` §4 for the shared baseline (secrets never
   committed, allow-listed CORS, unprivileged container user, no stack
   traces in API responses).

**Not implemented in this submission, called out explicitly:** per-user
authentication/dataset ownership (any uploaded dataset is currently visible
to any caller — there's no user model in either task's brief), and
enforcement of the `AI_ASSISTANT`-equivalent rate limit for Task 2's
`/query` and `/export` endpoints (same gap as Task 1, same reasoning —
flagged rather than silently absent).

## 5. Challenges Faced and Solutions Implemented

- **Column names as an injection surface, not just query text.** The
  obvious SQL-injection risk in a "natural language to SQL" feature is the
  *question* the user types. The less obvious one — and the one that's easy
  to miss — is that in Task 2, the **uploaded file's own column headers**
  become part of `CREATE TABLE`/`INSERT` statements, and Postgres offers no
  parameter binding for identifiers (only for values). A header like
  `"; DROP TABLE users; --` isn't hypothetical; it's exactly the kind of
  thing an adversarial or just-malformed CSV export can contain. Solved by
  never using upload-derived text as an identifier at all — table names are
  server-generated UUIDs, column names are passed through a strict allow-list
  sanitizer (`[a-z0-9_]` only) with the *original* name preserved separately,
  purely for display. Covered by `test_sanitizes_sql_injection_attempt_in_header`
  and 9 related tests.
- **sqlglot's internal AST shape isn't stable across versions.** An early
  version of the validator read `stmt.args.get("with")` to detect CTEs,
  which worked against one sqlglot version's parse tree but silently
  returned `None` against the version actually pinned in `requirements.txt`
  (the arg key changed to `with_` between versions). A CTE query was
  therefore incorrectly rejected as "referencing an unauthorized table" —
  the outer query's reference to its own CTE alias (`SELECT * FROM ranked`)
  looked like a foreign table because the CTE's alias wasn't being
  recognized as one at all. Fixed by walking the tree for
  `exp.With`/`exp.CTE` **node types** instead of reading version-specific
  argument dictionary keys, which is stable regardless of sqlglot's internal
  renames. This was caught by `test_cte_select_allowed` failing during
  development, before it could reach a real user's query.
- **pandas' default dtype for text columns is not consistent across
  versions.** Type inference initially checked `df[col].dtype == "object"`
  to find string columns worth attempting a date-parse on. This works on
  pandas 2.x but pandas 3.x's default text dtype prints as `str`/a
  PyArrow-backed extension type, not `object` — so the exact-string check
  silently stopped detecting date columns, and every date column downgraded
  to `TEXT` instead of `TIMESTAMP`. Fixed by switching to
  `pandas.api.types.is_object_dtype`/`is_string_dtype`
  (capability-based checks) instead of comparing dtype to a literal string —
  caught by `test_infer_schema_detects_date_columns` failing in CI-equivalent
  local testing before it shipped.
- **Where to bound "arbitrary dataset" pragmatically.** Fully generic
  ingestion could mean supporting nested JSON, multi-sheet Excel files,
  mixed-type columns, and arbitrarily wide files. Scoped explicitly to flat
  CSV/single-sheet Excel with pandas' own type inference plus a >90%-parse
  heuristic for date columns — documented here rather than silently handling
  edge cases inconsistently. A column that's 95% numbers and 5% garbage text
  currently becomes `TEXT` (pandas' inference falls back to object/string for
  the whole column), which is the safe direction to fail in for a query tool
  — over-eager numeric coercion that silently drops malformed rows would be
  worse than a column that's queryable but requires a `CAST` in generated SQL.
