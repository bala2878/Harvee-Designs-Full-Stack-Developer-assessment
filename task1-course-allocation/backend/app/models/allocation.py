import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import AllocationRunStatusEnum, AllocationStatusEnum


class CoursePreference(Base):

    __tablename__ = "course_preferences"
    __table_args__ = (
        UniqueConstraint("student_id", "priority", name="uq_student_priority"),
        UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3 ...

    student: Mapped["Student"] = relationship(back_populates="preferences")
    course: Mapped["Course"] = relationship(back_populates="preferences")


class Allocation(Base):

    __tablename__ = "allocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    allocation_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("allocation_runs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[AllocationStatusEnum] = mapped_column(
        Enum(AllocationStatusEnum, name="allocation_status_enum", create_type=False), nullable=False
    )
    preference_rank_matched: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 1 if got 1st preference, 2 if 2nd, etc. None if not allocated
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "allocated under SC quota"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["Student"] = relationship(back_populates="allocation")
    course: Mapped["Course | None"] = relationship(back_populates="allocations")
    allocation_run: Mapped["AllocationRun"] = relationship(back_populates="allocations")


class AllocationRun(Base):
    
    __tablename__ = "allocation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[AllocationRunStatusEnum] = mapped_column(
        Enum(AllocationRunStatusEnum, name="allocation_run_status_enum", create_type=False),
        default=AllocationRunStatusEnum.PENDING,
    )
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    total_allocated: Mapped[int] = mapped_column(Integer, default=0)
    total_unallocated: Mapped[int] = mapped_column(Integer, default=0)
    triggered_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    allocations: Mapped[list["Allocation"]] = relationship(back_populates="allocation_run")
