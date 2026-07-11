from fastapi import APIRouter

from app.api.v1 import datasets, query

api_router = APIRouter()
api_router.include_router(datasets.router)
api_router.include_router(query.router)
