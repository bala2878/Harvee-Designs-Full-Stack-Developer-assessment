from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.allocation import Allocation, AllocationRun, CoursePreference
from app.models.course import Course
from app.models.enums import AllocationRunStatusEnum
from app.models.student import Student
from app.services.allocation_engine import CourseInput, StudentInput, run_allocation


async def execute_allocation_run(db: AsyncSession, triggered_by: str | None = None) -> AllocationRun:
    run = AllocationRun(status=AllocationRunStatusEnum.RUNNING, triggered_by=triggered_by)
    db.add(run)
    await db.flush()

    try:
        student_rows = await db.execute(
            select(Student).options(selectinload(Student.preferences))
        )
        students = student_rows.scalars().all()

        course_rows = await db.execute(select(Course).options(selectinload(Course.seat_reservations)))
        courses = course_rows.scalars().all()

        student_inputs = [
            StudentInput(
                id=s.id,
                marks=s.marks,
                application_date=s.application_date,
                category=s.category,
                preference_course_ids=[p.course_id for p in sorted(s.preferences, key=lambda p: p.priority)],
            )
            for s in students
        ]
        course_inputs = [
            CourseInput(
                id=c.id,
                total_seats=c.total_seats,
                reserved_seats={r.category: r.reserved_seats for r in c.seat_reservations},
            )
            for c in courses
        ]

        results = run_allocation(student_inputs, course_inputs)
        await db.execute(delete(Allocation))
        await db.flush()

        allocated_count = 0
        for r in results:
            db.add(
                Allocation(
                    student_id=r.student_id,
                    course_id=r.course_id,
                    allocation_run_id=run.id,
                    status=r.status,
                    preference_rank_matched=r.preference_rank_matched,
                    reason=r.reason,
                )
            )
            if r.course_id is not None:
                allocated_count += 1

        from datetime import datetime, timezone

        run.status = AllocationRunStatusEnum.COMPLETED
        run.total_students = len(results)
        run.total_allocated = allocated_count
        run.total_unallocated = len(results) - allocated_count
        run.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(run)
        return run

    except Exception:
        run.status = AllocationRunStatusEnum.FAILED
        await db.commit()
        raise
