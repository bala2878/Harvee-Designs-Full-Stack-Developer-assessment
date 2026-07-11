from fastapi import APIRouter

from app.api.v1 import ai_assistant, allocation, courses, students

api_router = APIRouter()
api_router.include_router(students.router)
api_router.include_router(courses.router)
api_router.include_router(allocation.router)
api_router.include_router(ai_assistant.router)
