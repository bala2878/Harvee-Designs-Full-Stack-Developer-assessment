import re
import uuid
from io import BytesIO

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.dataset import Dataset

_IDENTIFIER_RE = re.compile(r"[^a-z0-9_]")


class DatasetIngestionError(Exception):
    pass


def _sanitize_identifier(raw: str, fallback_index: int) -> str:
    name = raw.strip().lower().replace(" ", "_").replace("-", "_")
    name = _IDENTIFIER_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name or not name[0].isalpha():
        name = f"col_{fallback_index}" if not name else f"c_{name}"
    return name[:63]


def _dedupe(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result = []
    for n in names:
        if n not in seen:
            seen[n] = 0
            result.append(n)
        else:
            seen[n] += 1
            result.append(f"{n}_{seen[n]}")
    return result


def _read_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
    elif filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes))
    else:
        raise DatasetIngestionError("Unsupported file type. Upload a .csv or .xlsx/.xls file.")

    if df.empty:
        raise DatasetIngestionError("The uploaded file has no rows.")
    if len(df) > settings.MAX_UPLOAD_ROWS:
        raise DatasetIngestionError(
            f"File has {len(df)} rows, exceeding the {settings.MAX_UPLOAD_ROWS}-row limit for this assessment build."
        )
    return df


def _infer_schema(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:

    original_names = [str(c) for c in df.columns]
    sanitized = _dedupe([_sanitize_identifier(c, i) for i, c in enumerate(original_names)])

    df = df.copy()
    df.columns = sanitized

    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.9:  # >90% parse successfully -> treat as a date column
                df[col] = parsed

    columns_metadata = []
    for original, sanitized_name in zip(original_names, sanitized):
        pg_type = _map_pg_type(df[sanitized_name])
        columns_metadata.append(
            {"original_name": original, "column_name": sanitized_name, "data_type": pg_type}
        )
    return df, columns_metadata


def _map_pg_type(series: pd.Series) -> str:

    if pd.api.types.is_bool_dtype(series):
        return "BOOLEAN"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "TIMESTAMP"
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "DOUBLE PRECISION"
    return "TEXT"


async def ingest_dataset(db: AsyncSession, file_bytes: bytes, filename: str, display_name: str) -> Dataset:
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise DatasetIngestionError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit.")

    df = _read_dataframe(file_bytes, filename)
    df, columns_metadata = _infer_schema(df)

    table_name = f"ds_{uuid.uuid4().hex[:12]}" 
    schema = settings.DATASET_SCHEMA

    await db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    column_defs = ", ".join(f'"{c["column_name"]}" {c["data_type"]}' for c in columns_metadata)
    await db.execute(text(f'CREATE TABLE "{schema}"."{table_name}" ({column_defs})'))

    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    if records:
        col_names = [c["column_name"] for c in columns_metadata]
        placeholders = ", ".join(f":{c}" for c in col_names)
        col_list = ", ".join(f'"{c}"' for c in col_names)
        insert_stmt = text(f'INSERT INTO "{schema}"."{table_name}" ({col_list}) VALUES ({placeholders})')
        chunk_size = 2000
        for i in range(0, len(records), chunk_size):
            await db.execute(insert_stmt, records[i : i + chunk_size])

    dataset = Dataset(
        name=display_name,
        original_filename=filename,
        file_type="csv" if filename.lower().endswith(".csv") else "xlsx",
        table_name=table_name,
        row_count=len(df),
        columns_metadata=columns_metadata,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


async def drop_dataset_table(db: AsyncSession, dataset: Dataset) -> None:
    await db.execute(text(f'DROP TABLE IF EXISTS "{settings.DATASET_SCHEMA}"."{dataset.table_name}"'))
    await db.delete(dataset)
    await db.commit()
