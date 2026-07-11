from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.models.allocation import Allocation, AllocationRun, CoursePreference
from app.models.course import Course
from app.models.enums import AllocationStatusEnum
from app.models.student import Student
from app.schemas.allocation import AllocationOut, AllocationRunOut, DashboardSummaryOut
from app.services.allocation_orchestrator import execute_allocation_run

router = APIRouter(tags=["Allocation"])


@router.post("/allocation/run", response_model=AllocationRunOut, status_code=201)
async def trigger_allocation_run(db: AsyncSession = Depends(get_db)):
    """Runs the full merit + reservation + preference allocation algorithm.
    Re-running replaces all prior allocation results (single active round)."""
    run = await execute_allocation_run(db, triggered_by="api")
    return run


@router.get("/allocation/results", response_model=list[AllocationOut])
async def get_allocation_results(
    status: AllocationStatusEnum | None = None,
    course_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Allocation)
        .options(selectinload(Allocation.student), selectinload(Allocation.course))
        .join(Student, Allocation.student_id == Student.id)
    )
    if status:
        query = query.where(Allocation.status == status)
    if course_id:
        query = query.where(Allocation.course_id == course_id)

    result = await db.execute(query.order_by(Student.marks.desc()))
    allocations = result.scalars().all()

    return [
        AllocationOut(
            student_id=a.student_id,
            student_name=a.student.name,
            student_code=a.student.student_code,
            category=a.student.category.value,
            course_id=a.course_id,
            course_name=a.course.name if a.course else None,
            status=a.status,
            preference_rank_matched=a.preference_rank_matched,
            reason=a.reason,
        )
        for a in allocations
    ]


@router.get("/allocation/runs", response_model=list[AllocationRunOut])
async def list_allocation_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AllocationRun).order_by(AllocationRun.started_at.desc()))
    return result.scalars().all()


@router.get("/dashboard/summary", response_model=DashboardSummaryOut)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    total_students = await db.scalar(select(func.count()).select_from(Student)) or 0
    total_courses = await db.scalar(select(func.count()).select_from(Course)) or 0
    total_seats = await db.scalar(select(func.coalesce(func.sum(Course.total_seats), 0))) or 0

    total_allocated = (
        await db.scalar(
            select(func.count())
            .select_from(Allocation)
            .where(Allocation.status == AllocationStatusEnum.ALLOCATED)
        )
        or 0
    )
    total_unallocated = (
        await db.scalar(
            select(func.count())
            .select_from(Allocation)
            .where(Allocation.status == AllocationStatusEnum.NOT_ALLOCATED)
        )
        or 0
    )

    cat_result = await db.execute(
        select(Student.category, func.count())
        .join(Allocation, Allocation.student_id == Student.id)
        .where(Allocation.status == AllocationStatusEnum.ALLOCATED)
        .group_by(Student.category)
    )
    category_wise = {cat.value: cnt for cat, cnt in cat_result.all()}

    first_pref_matches = (
        await db.scalar(
            select(func.count())
            .select_from(Allocation)
            .where(Allocation.preference_rank_matched == 1)
        )
        or 0
    )
    first_pref_rate = round((first_pref_matches / total_allocated) * 100, 2) if total_allocated else 0.0

    latest_run_result = await db.execute(select(AllocationRun).order_by(AllocationRun.started_at.desc()).limit(1))
    latest_run = latest_run_result.scalar_one_or_none()

    return DashboardSummaryOut(
        total_students=total_students,
        total_courses=total_courses,
        total_seats=total_seats,
        total_allocated=total_allocated,
        total_unallocated=total_unallocated,
        overall_fill_rate_percent=round((total_allocated / total_seats) * 100, 2) if total_seats else 0.0,
        category_wise_allocation=category_wise,
        first_preference_match_rate_percent=first_pref_rate,
        latest_run=latest_run,
    )
