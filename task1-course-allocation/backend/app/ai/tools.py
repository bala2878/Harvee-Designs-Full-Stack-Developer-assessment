from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allocation import Allocation, CoursePreference
from app.models.course import Course
from app.models.enums import AllocationStatusEnum
from app.models.student import Student

# --- Tool schema definitions (OpenAI function-calling format) ----

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_allocation_count_per_course",
            "description": "Returns the number of students allocated to each course. Use for questions like "
            "'how many students were allocated to each course'.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_students_without_first_preference",
            "description": "Returns students who were allocated but NOT to their 1st preference course "
            "(i.e. preference_rank_matched > 1), including which rank they did get.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_course_rejection_rates",
            "description": "Returns each course's rejection rate: percentage of students who listed the course as "
            "a preference but were not ultimately allocated to it. Use for 'which course had the highest "
            "rejection rate'.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_wise_allocation_summary",
            "description": "Returns the count of allocated students broken down by reservation category "
            "(GENERAL/OBC/SC/ST), optionally filtered to one course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "Optional course name to filter the summary to a single course.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_unallocated_students",
            "description": "Returns students who received no allocation at all in the latest run.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# --- Tool implementations ----


async def get_allocation_count_per_course(db: AsyncSession, **_) -> list[dict]:
    result = await db.execute(
        select(Course.name, func.count(Allocation.id))
        .join(Allocation, Allocation.course_id == Course.id)
        .where(Allocation.status == AllocationStatusEnum.ALLOCATED)
        .group_by(Course.name)
        .order_by(func.count(Allocation.id).desc())
    )
    return [{"course": name, "allocated_count": cnt} for name, cnt in result.all()]


async def get_students_without_first_preference(db: AsyncSession, **_) -> list[dict]:
    result = await db.execute(
        select(Student.name, Student.student_code, Course.name, Allocation.preference_rank_matched)
        .join(Allocation, Allocation.student_id == Student.id)
        .join(Course, Allocation.course_id == Course.id)
        .where(Allocation.status == AllocationStatusEnum.ALLOCATED, Allocation.preference_rank_matched > 1)
        .order_by(Allocation.preference_rank_matched)
    )
    return [
        {"student": name, "student_code": code, "allocated_course": course, "preference_rank_received": rank}
        for name, code, course, rank in result.all()
    ]


async def get_course_rejection_rates(db: AsyncSession, **_) -> list[dict]:
    courses_result = await db.execute(select(Course.id, Course.name))
    courses = courses_result.all()

    output = []
    for course_id, name in courses:
        total_preferred = await db.scalar(
            select(func.count(func.distinct(CoursePreference.student_id))).where(
                CoursePreference.course_id == course_id
            )
        )
        allocated = await db.scalar(
            select(func.count()).where(
                Allocation.course_id == course_id, Allocation.status == AllocationStatusEnum.ALLOCATED
            )
        )
        total_preferred = total_preferred or 0
        allocated = allocated or 0
        rejected = max(total_preferred - allocated, 0)
        rate = round((rejected / total_preferred) * 100, 2) if total_preferred else 0.0
        output.append({"course": name, "rejection_rate_percent": rate, "total_preferred": total_preferred})

    output.sort(key=lambda x: x["rejection_rate_percent"], reverse=True)
    return output


async def get_category_wise_allocation_summary(db: AsyncSession, course_name: str | None = None, **_) -> list[dict]:
    query = (
        select(Student.category, func.count())
        .join(Allocation, Allocation.student_id == Student.id)
        .where(Allocation.status == AllocationStatusEnum.ALLOCATED)
        .group_by(Student.category)
    )
    if course_name:
        query = query.join(Course, Allocation.course_id == Course.id).where(Course.name.ilike(f"%{course_name}%"))

    result = await db.execute(query)
    return [{"category": cat.value, "allocated_count": cnt} for cat, cnt in result.all()]


async def get_unallocated_students(db: AsyncSession, **_) -> list[dict]:
    result = await db.execute(
        select(Student.name, Student.student_code, Student.category)
        .join(Allocation, Allocation.student_id == Student.id)
        .where(Allocation.status == AllocationStatusEnum.NOT_ALLOCATED)
    )
    return [{"student": name, "student_code": code, "category": cat.value} for name, code, cat in result.all()]


TOOL_IMPLEMENTATIONS = {
    "get_allocation_count_per_course": get_allocation_count_per_course,
    "get_students_without_first_preference": get_students_without_first_preference,
    "get_course_rejection_rates": get_course_rejection_rates,
    "get_category_wise_allocation_summary": get_category_wise_allocation_summary,
    "get_unallocated_students": get_unallocated_students,
}