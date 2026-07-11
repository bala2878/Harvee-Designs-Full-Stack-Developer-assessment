import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetOut
from app.services.dataset_service import DatasetIngestionError, drop_dataset_table, ingest_dataset

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetOut, status_code=201)
async def upload_dataset(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    try:
        dataset = await ingest_dataset(
            db, file_bytes, file.filename, display_name=file.filename.rsplit(".", 1)[0]
        )
    except DatasetIngestionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return dataset


@router.get("", response_model=list[DatasetOut])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    return result.scalars().all()


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    dataset = await db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    dataset = await db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    await drop_dataset_table(db, dataset)
