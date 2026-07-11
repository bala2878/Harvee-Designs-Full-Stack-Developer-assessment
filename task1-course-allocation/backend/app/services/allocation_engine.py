from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from app.models.enums import AllocationStatusEnum, CategoryEnum


@dataclass
class StudentInput:
    id: uuid.UUID
    marks: float
    application_date: object
    category: CategoryEnum
    preference_course_ids: list[uuid.UUID]


@dataclass
class CourseInput:
    id: uuid.UUID
    total_seats: int
    reserved_seats: dict[CategoryEnum, int] = field(default_factory=dict)


@dataclass
class AllocationResult:
    student_id: uuid.UUID
    course_id: uuid.UUID | None
    status: AllocationStatusEnum
    preference_rank_matched: int | None
    reason: str


class _CourseSeatPool:

    __slots__ = ("course_id", "reserved_remaining", "general_remaining")

    def __init__(self, course: CourseInput):
        self.course_id = course.id
        reserved_total = sum(
            v for k, v in course.reserved_seats.items() if k != CategoryEnum.GENERAL
        )
        self.reserved_remaining: dict[CategoryEnum, int] = {
            cat: seats for cat, seats in course.reserved_seats.items() if cat != CategoryEnum.GENERAL
        }
        self.general_remaining = max(course.total_seats - reserved_total, 0)

    def try_seat(self, category: CategoryEnum) -> tuple[bool, str]:

        if category in self.reserved_remaining and self.reserved_remaining[category] > 0:
            self.reserved_remaining[category] -= 1
            return True, f"allocated under {category.value} reserved quota"
        
        if self.general_remaining > 0:
            self.general_remaining -= 1
            return True, "allocated under general/merit quota"
        return False, "no seats remaining in preferred category or general pool"


def run_allocation(students: list[StudentInput], courses: list[CourseInput]) -> list[AllocationResult]:

    ranked_students = sorted(
        students,
        key=lambda s: (-s.marks, s.application_date),
    )

    pools: dict[uuid.UUID, _CourseSeatPool] = {c.id: _CourseSeatPool(c) for c in courses}

    results: list[AllocationResult] = []

    for student in ranked_students:
        allocated = False
        for rank, course_id in enumerate(student.preference_course_ids, start=1):
            pool = pools.get(course_id)
            if pool is None:
                continue 
            seated, reason = pool.try_seat(student.category)
            if seated:
                results.append(
                    AllocationResult(
                        student_id=student.id,
                        course_id=course_id,
                        status=AllocationStatusEnum.ALLOCATED,
                        preference_rank_matched=rank,
                        reason=reason,
                    )
                )
                allocated = True
                break
        if not allocated:
            results.append(
                AllocationResult(
                    student_id=student.id,
                    course_id=None,
                    status=AllocationStatusEnum.NOT_ALLOCATED,
                    preference_rank_matched=None,
                    reason="no seats available in any preferred course for this student's category",
                )
            )

    return results
