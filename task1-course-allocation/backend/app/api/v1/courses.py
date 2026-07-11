import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.course import CourseCreate, CourseOut, CourseStatsOut, CourseUpdate
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("", response_model=CourseOut, status_code=201)
async def create_course(payload: CourseCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await course_service.create_course(db, payload)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A course with this name or code already exists") from e


@router.get("", response_model=list[CourseOut])
async def list_courses(db: AsyncSession = Depends(get_db)):
    return await course_service.list_courses(db)


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    course = await course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/stats", response_model=CourseStatsOut)
async def get_course_stats(course_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    course = await course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    stats = await course_service.get_course_stats(db, course)
    return CourseStatsOut(
        id=course.id,
        name=course.name,
        code=course.code,
        total_seats=course.total_seats,
        created_at=course.created_at,
        **stats,
    )


@router.patch("/{course_id}", response_model=CourseOut)
async def update_course(course_id: uuid.UUID, payload: CourseUpdate, db: AsyncSession = Depends(get_db)):
    course = await course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return await course_service.update_course(db, course, payload)


@router.delete("/{course_id}", status_code=204)
async def delete_course(course_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    course = await course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    await course_service.delete_course(db, course)
