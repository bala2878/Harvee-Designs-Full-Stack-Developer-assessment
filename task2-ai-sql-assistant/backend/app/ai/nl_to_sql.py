from openai import AsyncOpenAI

from app.core.config import settings
from app.models.dataset import Dataset

SYSTEM_PROMPT_TEMPLATE = """You are a PostgreSQL query generator. Given a dataset's schema and a
natural-language question, output EXACTLY ONE valid PostgreSQL SELECT statement that answers it —
nothing else. No markdown code fences, no explanation, no semicolon-terminated multiple statements.

Rules:
- Query ONLY the table "{schema}"."{table}" — it is the only table available to you.
- Use ONLY these columns (exact names, case-sensitive): {columns}
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, GRANT, or any statement other than SELECT.
- Prefer aggregate functions (COUNT, SUM, AVG, MIN, MAX) and GROUP BY for summary questions.
- For "top N" questions, use ORDER BY ... LIMIT N.
- For "duplicate records", use GROUP BY across all columns HAVING COUNT(*) > 1.
- For "missing values", use IS NULL checks on the relevant column(s), or across all columns with OR if
  the question doesn't name a specific column.
- If the question is ambiguous, make the most reasonable interpretation rather than asking for
  clarification — you must always return a SQL query.
- Output ONLY the raw SQL. Do not wrap it in ```sql fences or add commentary.
"""


class SQLGenerationError(Exception):
    pass


def _build_system_prompt(dataset: Dataset) -> str:
    columns_desc = ", ".join(f'"{c["column_name"]}" ({c["data_type"]})' for c in dataset.columns_metadata)
    return SYSTEM_PROMPT_TEMPLATE.format(
        schema=settings.DATASET_SCHEMA, table=dataset.table_name, columns=columns_desc
    )


async def generate_sql(dataset: Dataset, question: str) -> str:
    if not settings.OPENAI_API_KEY:
        raise SQLGenerationError(
            "OPENAI_API_KEY is not configured. Set it in the environment to enable the AI SQL assistant."
        )

    client = AsyncOpenAI(api_key="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")
    response = await client.chat.completions.create(
        model=settings.AI_MODEL,
        max_tokens=512,
        messages=[
            {"role": "system", "content": _build_system_prompt(dataset)},
            {"role": "user", "content": question},
        ],
    )

    raw_sql = (response.choices[0].message.content or "").strip()

    if raw_sql.startswith("```"):
        raw_sql = raw_sql.strip("`")
        if raw_sql.lower().startswith("sql"):
            raw_sql = raw_sql[3:].strip()

    if not raw_sql:
        raise SQLGenerationError("The AI model returned an empty response.")

    return raw_sql