import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.allocation import Allocation, CoursePreference
from app.models.course import Course, CourseSeatReservation
from app.models.enums import AllocationStatusEnum
from app.schemas.course import CourseCreate, CourseUpdate


async def create_course(db: AsyncSession, payload: CourseCreate) -> Course:
    course = Course(name=payload.name, code=payload.code, total_seats=payload.total_seats)
    db.add(course)
    await db.flush()
    for r in payload.reservations:
        db.add(CourseSeatReservation(course_id=course.id, category=r.category, reserved_seats=r.reserved_seats))
    await db.commit()
    await db.refresh(course, attribute_names=["seat_reservations"])
    return course


async def list_courses(db: AsyncSession) -> list[Course]:
    result = await db.execute(select(Course).options(selectinload(Course.seat_reservations)))
    return list(result.scalars().all())


async def get_course(db: AsyncSession, course_id: uuid.UUID) -> Course | None:
    result = await db.execute(
        select(Course).options(selectinload(Course.seat_reservations)).where(Course.id == course_id)
    )
    return result.scalar_one_or_none()


async def update_course(db: AsyncSession, course: Course, payload: CourseUpdate) -> Course:
    if payload.name is not None:
        course.name = payload.name
    if payload.total_seats is not None:
        course.total_seats = payload.total_seats
    if payload.reservations is not None:
        for res in course.seat_reservations:
            await db.delete(res)
        await db.flush()
        for r in payload.reservations:
            db.add(CourseSeatReservation(course_id=course.id, category=r.category, reserved_seats=r.reserved_seats))
    await db.commit()
    await db.refresh(course, attribute_names=["seat_reservations"])
    return course


async def delete_course(db: AsyncSession, course: Course) -> None:
    await db.delete(course)
    await db.commit()


async def get_course_stats(db: AsyncSession, course: Course) -> dict:
    allocated_count = await db.scalar(
        select(func.count())
        .select_from(Allocation)
        .where(Allocation.course_id == course.id, Allocation.status == AllocationStatusEnum.ALLOCATED)
    )
    allocated_count = allocated_count or 0

    from app.models.student import Student  # local import to avoid circular import at module load

    cat_result = await db.execute(
        select(Student.category, func.count())
        .join(Allocation, Allocation.student_id == Student.id)
        .where(Allocation.course_id == course.id, Allocation.status == AllocationStatusEnum.ALLOCATED)
        .group_by(Student.category)
    )
    category_wise = {cat.value: cnt for cat, cnt in cat_result.all()}


    total_preferred = await db.scalar(
        select(func.count(func.distinct(CoursePreference.student_id))).where(
            CoursePreference.course_id == course.id
        )
    )
    total_preferred = total_preferred or 0
    rejected = max(total_preferred - allocated_count, 0)
    rejection_rate = round((rejected / total_preferred) * 100, 2) if total_preferred else 0.0

    return {
        "seats_filled": allocated_count,
        "seats_available": max(course.total_seats - allocated_count, 0),
        "category_wise_allocations": category_wise,
        "rejection_rate_percent": rejection_rate,
    }
