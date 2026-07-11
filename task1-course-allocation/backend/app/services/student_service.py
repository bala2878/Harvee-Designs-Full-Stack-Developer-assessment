import uuid
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.allocation import CoursePreference
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


async def _next_student_code(db: AsyncSession) -> str:
    year = date.today().year
    count = await db.scalar(select(func.count()).select_from(Student))
    return f"STU-{year}-{(count or 0) + 1:04d}"


async def create_student(db: AsyncSession, payload: StudentCreate) -> Student:
    student = Student(
        student_code=await _next_student_code(db),
        name=payload.name,
        email=payload.email,
        marks=payload.marks,
        category=payload.category,
        application_date=payload.application_date or date.today(),
    )
    db.add(student)
    await db.flush()

    for pref in payload.preferences:
        db.add(CoursePreference(student_id=student.id, course_id=pref.course_id, priority=pref.priority))

    await db.commit()
    await db.refresh(student, attribute_names=["preferences", "allocation"])
    return student


async def get_student(db: AsyncSession, student_id: uuid.UUID) -> Student | None:
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.preferences), selectinload(Student.allocation))
        .where(Student.id == student_id)
    )
    return result.scalar_one_or_none()


async def list_students(
    db: AsyncSession, skip: int = 0, limit: int = 50, category: str | None = None
) -> tuple[list[Student], int]:
    query = select(Student).options(selectinload(Student.preferences), selectinload(Student.allocation))
    count_query = select(func.count()).select_from(Student)
    if category:
        query = query.where(Student.category == category)
        count_query = count_query.where(Student.category == category)

    total = await db.scalar(count_query)
    result = await db.execute(query.order_by(Student.marks.desc()).offset(skip).limit(limit))
    return list(result.scalars().all()), total or 0


async def update_student(db: AsyncSession, student: Student, payload: StudentUpdate) -> Student:
    if payload.name is not None:
        student.name = payload.name
    if payload.marks is not None:
        student.marks = payload.marks
    if payload.category is not None:
        student.category = payload.category
    if payload.preferences is not None:
        student.preferences.clear()
        await db.flush()
        for pref in payload.preferences:
            db.add(CoursePreference(student_id=student.id, course_id=pref.course_id, priority=pref.priority))
    await db.commit()
    await db.refresh(student, attribute_names=["preferences", "allocation"])
    return student


async def delete_student(db: AsyncSession, student: Student) -> None:
    await db.delete(student)
    await db.commit()
