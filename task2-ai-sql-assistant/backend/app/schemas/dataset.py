import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ColumnMetadataOut(BaseModel):
    original_name: str
    column_name: str
    data_type: str


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    original_filename: str
    file_type: str
    row_count: int
    columns_metadata: list[ColumnMetadataOut]
    created_at: datetime


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class QueryResultOut(BaseModel):
    question: str
    generated_sql: str
    columns: list[str]
    rows: list[dict]
    row_count: int
    execution_ms: int


class QueryHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    generated_sql: str
    row_count_returned: int | None
    success: bool
    error_message: str | None
    execution_ms: int | None
    created_at: datetime


class InsightsOut(BaseModel):
    dataset_id: uuid.UUID
    insights: str
