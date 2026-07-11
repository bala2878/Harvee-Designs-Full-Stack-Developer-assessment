import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CategoryEnum


class SeatReservationIn(BaseModel):
    category: CategoryEnum
    reserved_seats: int = Field(ge=0)


class CourseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=20)
    total_seats: int = Field(gt=0)
    reservations: list[SeatReservationIn] = []

    @field_validator("reservations")
    @classmethod
    def reservations_cannot_exceed_total(cls, v, info):
        total_reserved = sum(r.reserved_seats for r in v if r.category != CategoryEnum.GENERAL)
        total_seats = info.data.get("total_seats")
        if total_seats is not None and total_reserved > total_seats:
            raise ValueError("sum of reserved seats cannot exceed total_seats")
        return v


class CourseUpdate(BaseModel):
    name: str | None = None
    total_seats: int | None = Field(default=None, gt=0)
    reservations: list[SeatReservationIn] | None = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    total_seats: int
    created_at: datetime


class CourseStatsOut(CourseOut):
    seats_filled: int
    seats_available: int
    category_wise_allocations: dict[str, int]
    rejection_rate_percent: float  # % of students who had this as a preference but were not allocated to it
