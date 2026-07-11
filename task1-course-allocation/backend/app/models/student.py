import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import CategoryEnum


class Student(Base):
    
    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_marks_desc", "marks", "application_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # human-readable e.g. STU-2026-0001
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    marks: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[CategoryEnum] = mapped_column(
        Enum(CategoryEnum, name="category_enum", create_type=False), nullable=False
    )
    application_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    preferences: Mapped[list["CoursePreference"]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="CoursePreference.priority"
    )
    allocation: Mapped["Allocation | None"] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
