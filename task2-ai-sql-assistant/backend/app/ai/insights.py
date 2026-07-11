from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.dataset import Dataset

INSIGHTS_SYSTEM_PROMPT = """You are a data analyst. Given a dataset's schema and summary statistics,
write a concise (4-6 sentences) narrative of what stands out: data quality issues (missing values,
possible duplicates), notable ranges/distributions, and one or two suggested questions the user might
want to ask next. Do not restate the raw numbers mechanically — synthesize them into observations.
Plain text only, no markdown headers."""


async def _compute_quick_stats(readonly_db: AsyncSession, dataset: Dataset) -> dict:
    schema, table = settings.DATASET_SCHEMA, dataset.table_name
    stats: dict = {"row_count": dataset.row_count, "columns": {}}

    null_check_parts = ", ".join(
        f'SUM(CASE WHEN "{c["column_name"]}" IS NULL THEN 1 ELSE 0 END) AS "{c["column_name"]}_nulls"'
        for c in dataset.columns_metadata
    )
    if null_check_parts:
        result = await readonly_db.execute(text(f'SELECT {null_check_parts} FROM "{schema}"."{table}"'))
        row = result.mappings().first()
        if row:
            for c in dataset.columns_metadata:
                stats["columns"][c["column_name"]] = {
                    "data_type": c["data_type"],
                    "null_count": row.get(f"{c['column_name']}_nulls", 0),
                }

    return stats


async def generate_insights(readonly_db: AsyncSession, dataset: Dataset) -> str:
    if not settings.OPENAI_API_KEY:
        return "AI insights unavailable: OPENAI_API_KEY is not configured."

    stats = await _compute_quick_stats(readonly_db, dataset)

    columns_desc = "\n".join(
        f"- {name}: type={info['data_type']}, null_count={info['null_count']}"
        for name, info in stats["columns"].items()
    )
    prompt = (
        f"Dataset: {dataset.name}\nTotal rows: {stats['row_count']}\n\nColumns:\n{columns_desc}"
    )

    client = AsyncOpenAI(api_key="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")
    response = await client.chat.completions.create(
        model=settings.AI_MODEL,
        max_tokens=400,
        messages=[
            {"role": "system", "content": INSIGHTS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()