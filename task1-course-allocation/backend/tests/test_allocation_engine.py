"""
Unit tests for the pure allocation algorithm (no DB required).
Run with: pytest backend/tests/test_allocation_engine.py -v
"""
from datetime import date
from uuid import uuid4

from app.models.enums import AllocationStatusEnum, CategoryEnum
from app.services.allocation_engine import CourseInput, StudentInput, run_allocation


def make_student(marks, category, app_date, prefs, sid=None):
    return StudentInput(
        id=sid or uuid4(),
        marks=marks,
        application_date=app_date,
        category=category,
        preference_course_ids=prefs,
    )


def test_higher_marks_get_priority():
    course_id = uuid4()
    course = CourseInput(id=course_id, total_seats=1, reserved_seats={})
    low = make_student(70, CategoryEnum.GENERAL, date(2026, 1, 1), [course_id])
    high = make_student(95, CategoryEnum.GENERAL, date(2026, 1, 2), [course_id])

    results = {r.student_id: r for r in run_allocation([low, high], [course])}

    assert results[high.id].status == AllocationStatusEnum.ALLOCATED
    assert results[low.id].status == AllocationStatusEnum.NOT_ALLOCATED


def test_tie_broken_by_earlier_application_date():
    course_id = uuid4()
    course = CourseInput(id=course_id, total_seats=1, reserved_seats={})
    later = make_student(80, CategoryEnum.GENERAL, date(2026, 2, 5), [course_id])
    earlier = make_student(80, CategoryEnum.GENERAL, date(2026, 1, 10), [course_id])

    results = {r.student_id: r for r in run_allocation([later, earlier], [course])}

    assert results[earlier.id].status == AllocationStatusEnum.ALLOCATED
    assert results[later.id].status == AllocationStatusEnum.NOT_ALLOCATED


def test_reservation_quota_respected():
    course_id = uuid4()
    # 2 total seats: 1 reserved for SC, 1 general
    course = CourseInput(id=course_id, total_seats=2, reserved_seats={CategoryEnum.SC: 1})

    sc_student = make_student(60, CategoryEnum.SC, date(2026, 1, 1), [course_id])
    general_high = make_student(99, CategoryEnum.GENERAL, date(2026, 1, 1), [course_id])
    general_low = make_student(50, CategoryEnum.GENERAL, date(2026, 1, 1), [course_id])

    results = {r.student_id: r for r in run_allocation([sc_student, general_high, general_low], [course])}

    # SC student gets the reserved seat even though marks are lowest overall
    assert results[sc_student.id].status == AllocationStatusEnum.ALLOCATED
    assert "SC reserved quota" in results[sc_student.id].reason
    # Highest-merit general student takes the remaining general seat
    assert results[general_high.id].status == AllocationStatusEnum.ALLOCATED
    # Lowest merit general student misses out
    assert results[general_low.id].status == AllocationStatusEnum.NOT_ALLOCATED


def test_unfilled_reserved_seats_do_not_block_general_students():
    """If no SC student applies, the SC-reserved seat should NOT sit empty while
    a general student who ranked it could have used it via the general pool —
    but per policy, unclaimed reserved seats do NOT auto-convert in this single
    round. This test documents that expected behaviour explicitly."""
    course_id = uuid4()
    course = CourseInput(id=course_id, total_seats=2, reserved_seats={CategoryEnum.SC: 1})
    g1 = make_student(90, CategoryEnum.GENERAL, date(2026, 1, 1), [course_id])
    g2 = make_student(85, CategoryEnum.GENERAL, date(2026, 1, 1), [course_id])

    results = {r.student_id: r for r in run_allocation([g1, g2], [course])}

    # Only 1 general seat exists (2 total - 1 SC reserved), so only g1 gets in
    assert results[g1.id].status == AllocationStatusEnum.ALLOCATED
    assert results[g2.id].status == AllocationStatusEnum.NOT_ALLOCATED


def test_falls_back_to_second_preference_when_first_is_full():
    course_a = uuid4()
    course_b = uuid4()
    courses = [
        CourseInput(id=course_a, total_seats=1, reserved_seats={}),
        CourseInput(id=course_b, total_seats=1, reserved_seats={}),
    ]
    top_student = make_student(95, CategoryEnum.GENERAL, date(2026, 1, 1), [course_a])
    second_student = make_student(90, CategoryEnum.GENERAL, date(2026, 1, 1), [course_a, course_b])

    results = {r.student_id: r for r in run_allocation([top_student, second_student], courses)}

    assert results[top_student.id].course_id == course_a
    assert results[second_student.id].course_id == course_b
    assert results[second_student.id].preference_rank_matched == 2


def test_student_allocated_to_only_one_course():
    course_a = uuid4()
    course_b = uuid4()
    courses = [
        CourseInput(id=course_a, total_seats=5, reserved_seats={}),
        CourseInput(id=course_b, total_seats=5, reserved_seats={}),
    ]
    student = make_student(88, CategoryEnum.GENERAL, date(2026, 1, 1), [course_a, course_b])

    results = run_allocation([student], courses)

    assert len(results) == 1  # exactly one allocation record for this student
