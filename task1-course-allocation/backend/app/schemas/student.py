import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import CategoryEnum


class PreferenceIn(BaseModel):
    course_id: uuid.UUID
    priority: int = Field(ge=1, le=10)

class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    marks: float = Field(ge=0, le=100)
    category: CategoryEnum
    application_date: date | None = None
    preferences: list[PreferenceIn] = Field(min_length=1, max_length=10)

    @field_validator("preferences")
    @classmethod
    def priorities_must_be_sequential_and_unique(cls, v: list[PreferenceIn]):
        priorities = sorted(p.priority for p in v)
        if priorities != list(range(1, len(priorities) + 1)):
            raise ValueError("preferences priorities must be sequential starting at 1 (1,2,3...) with no gaps/dupes")
        course_ids = [p.course_id for p in v]
        if len(course_ids) != len(set(course_ids)):
            raise ValueError("duplicate course in preferences is not allowed")
        return v


class StudentUpdate(BaseModel):
    name: str | None = None
    marks: float | None = Field(default=None, ge=0, le=100)
    category: CategoryEnum | None = None
    preferences: list[PreferenceIn] | None = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_code: str
    name: str
    email: str
    marks: float
    category: CategoryEnum
    application_date: date
    created_at: datetime


class StudentDetailOut(StudentOut):
    preferences: list[PreferenceIn] = []
    allocated_course_name: str | None = None
    allocation_status: str | None = None
