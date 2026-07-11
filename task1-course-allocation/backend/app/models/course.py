import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import CategoryEnum


class Course(Base):

    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. CSE, ECE
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    seat_reservations: Mapped[list["CourseSeatReservation"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    preferences: Mapped[list["CoursePreference"]] = relationship(back_populates="course")
    allocations: Mapped[list["Allocation"]] = relationship(back_populates="course")

    @property
    def general_seats(self) -> int:
        """Seats not carved out for any reserved category."""
        reserved = sum(r.reserved_seats for r in self.seat_reservations if r.category != CategoryEnum.GENERAL)
        return max(self.total_seats - reserved, 0)


class CourseSeatReservation(Base):

    __tablename__ = "course_seat_reservations"
    __table_args__ = (UniqueConstraint("course_id", "category", name="uq_course_category"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[CategoryEnum] = mapped_column(
        Enum(CategoryEnum, name="category_enum", create_type=False), nullable=False
    )
    reserved_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    course: Mapped["Course"] = relationship(back_populates="seat_reservations")
