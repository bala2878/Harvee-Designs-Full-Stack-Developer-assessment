import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.enums import CategoryEnum
from app.schemas.student import PreferenceIn, StudentCreate, StudentDetailOut, StudentOut, StudentUpdate
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=StudentDetailOut, status_code=201)
async def create_student(payload: StudentCreate, db: AsyncSession = Depends(get_db)):
    try:
        student = await student_service.create_student(db, payload)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A student with this email already exists") from e
    return _to_detail(student)


@router.get("", response_model=list[StudentOut])
async def list_students(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    category: CategoryEnum | None = None,
    db: AsyncSession = Depends(get_db),
):
    students, _total = await student_service.list_students(db, skip, limit, category.value if category else None)
    return students


@router.get("/{student_id}", response_model=StudentDetailOut)
async def get_student(student_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    student = await student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _to_detail(student)


@router.patch("/{student_id}", response_model=StudentDetailOut)
async def update_student(student_id: uuid.UUID, payload: StudentUpdate, db: AsyncSession = Depends(get_db)):
    student = await student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student = await student_service.update_student(db, student, payload)
    return _to_detail(student)


@router.delete("/{student_id}", status_code=204)
async def delete_student(student_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    student = await student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    await student_service.delete_student(db, student)


def _to_detail(student) -> StudentDetailOut:
    allocation = student.allocation
    return StudentDetailOut(
        id=student.id,
        student_code=student.student_code,
        name=student.name,
        email=student.email,
        marks=student.marks,
        category=student.category,
        application_date=student.application_date,
        created_at=student.created_at,
        preferences=[PreferenceIn(course_id=p.course_id, priority=p.priority) for p in student.preferences],
        allocated_course_name=allocation.course.name if allocation and allocation.course else None,
        allocation_status=allocation.status.value if allocation else None,
    )
