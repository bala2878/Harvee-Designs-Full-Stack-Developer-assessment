import time
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.nl_to_sql import SQLGenerationError, generate_sql
from app.ai.sql_validator import SQLValidationError, validate_and_prepare
from app.core.config import settings
from app.models.dataset import Dataset, QueryHistory

class QueryExecutionError(Exception):
    pass

async def run_natural_language_query(
    db: AsyncSession, readonly_db: AsyncSession, dataset: Dataset, question: str
) -> dict:
    """Full pipeline: NL question -> generated SQL -> validated SQL -> executed
    against the read-only role -> logged to query_history -> returned to caller.

    Every outcome (success or failure) is logged, so query_history is a
    complete record of what was asked, not just what succeeded.
    """
    allowed_table = f"{settings.DATASET_SCHEMA}.{dataset.table_name}"
    start = time.perf_counter()

    generated_sql = None
    safe_sql = None
    try:
        generated_sql = await generate_sql(dataset, question)
        safe_sql = validate_and_prepare(generated_sql, allowed_table)

        await readonly_db.execute(text(f"SET LOCAL statement_timeout = '{settings.QUERY_TIMEOUT_SECONDS}s'"))
        result = await readonly_db.execute(text(safe_sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        db.add(
            QueryHistory(
                dataset_id=dataset.id,
                question=question,
                generated_sql=safe_sql,
                row_count_returned=len(rows),
                success=True,
                execution_ms=elapsed_ms,
            )
        )
        await db.commit()

        return {
            "question": question,
            "generated_sql": safe_sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_ms": elapsed_ms,
        }

    except (SQLGenerationError, SQLValidationError, SQLAlchemyError, DBAPIError) as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        await readonly_db.rollback()
        db.add(
            QueryHistory(
                dataset_id=dataset.id,
                question=question,
                generated_sql=safe_sql or generated_sql or "",
                row_count_returned=None,
                success=False,
                error_message=str(e)[:1000],
                execution_ms=elapsed_ms,
            )
        )
        await db.commit()
        raise QueryExecutionError(str(e)) from e
