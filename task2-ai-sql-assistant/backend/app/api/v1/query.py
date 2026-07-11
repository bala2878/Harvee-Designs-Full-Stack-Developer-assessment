import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.insights import generate_insights
from app.core.db import get_db, get_readonly_db
from app.models.dataset import Dataset, QueryHistory
from app.schemas.dataset import InsightsOut, QueryHistoryOut, QueryRequest, QueryResultOut
from app.services import export_service
from app.services.query_service import QueryExecutionError, run_natural_language_query

router = APIRouter(tags=["Query"])


async def _get_dataset_or_404(db: AsyncSession, dataset_id: uuid.UUID) -> Dataset:
    dataset = await db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/datasets/{dataset_id}/query", response_model=QueryResultOut)
async def query_dataset(
    dataset_id: uuid.UUID,
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
    readonly_db: AsyncSession = Depends(get_readonly_db),
):
    dataset = await _get_dataset_or_404(db, dataset_id)
    try:
        result = await run_natural_language_query(db, readonly_db, dataset, payload.question)
    except QueryExecutionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return result


@router.get("/datasets/{dataset_id}/history", response_model=list[QueryHistoryOut])
async def get_query_history(
    dataset_id: uuid.UUID, limit: int = Query(default=50, le=200), db: AsyncSession = Depends(get_db)
):
    await _get_dataset_or_404(db, dataset_id)
    result = await db.execute(
        select(QueryHistory)
        .where(QueryHistory.dataset_id == dataset_id)
        .order_by(QueryHistory.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/datasets/{dataset_id}/insights", response_model=InsightsOut)
async def get_insights(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    readonly_db: AsyncSession = Depends(get_readonly_db),
):
    dataset = await _get_dataset_or_404(db, dataset_id)
    insights = await generate_insights(readonly_db, dataset)
    return InsightsOut(dataset_id=dataset.id, insights=insights)


@router.post("/datasets/{dataset_id}/export")
async def export_query_result(
    dataset_id: uuid.UUID,
    payload: QueryRequest,
    format: str = Query(default="xlsx", pattern="^(xlsx|csv|pdf)$"),
    db: AsyncSession = Depends(get_db),
    readonly_db: AsyncSession = Depends(get_readonly_db),
):

    dataset = await _get_dataset_or_404(db, dataset_id)
    try:
        result = await run_natural_language_query(db, readonly_db, dataset, payload.question)
    except QueryExecutionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    columns, rows = result["columns"], result["rows"]
    filename_base = f"{dataset.name}_query_result"

    if format == "csv":
        content = export_service.to_csv_bytes(columns, rows)
        media_type, filename = "text/csv", f"{filename_base}.csv"
    elif format == "pdf":
        content = export_service.to_pdf_bytes(dataset.name, columns, rows)
        media_type, filename = "application/pdf", f"{filename_base}.pdf"
    else:
        content = export_service.to_excel_bytes(columns, rows)
        media_type, filename = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            f"{filename_base}.xlsx",
        )

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
