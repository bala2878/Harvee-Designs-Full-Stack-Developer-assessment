import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AllocationRunStatusEnum, AllocationStatusEnum


class AllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID
    student_name: str
    student_code: str
    category: str
    course_id: uuid.UUID | None
    course_name: str | None
    status: AllocationStatusEnum
    preference_rank_matched: int | None
    reason: str | None


class AllocationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: AllocationRunStatusEnum
    total_students: int
    total_allocated: int
    total_unallocated: int
    triggered_by: str | None
    started_at: datetime
    completed_at: datetime | None


class DashboardSummaryOut(BaseModel):
    total_students: int
    total_courses: int
    total_seats: int
    total_allocated: int
    total_unallocated: int
    overall_fill_rate_percent: float
    category_wise_allocation: dict[str, int]
    first_preference_match_rate_percent: float
    latest_run: AllocationRunOut | None
