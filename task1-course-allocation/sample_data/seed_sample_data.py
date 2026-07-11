"""
Seeds the database with a realistic sample dataset: 8 courses (with a mix of
reserved-category seats) and 60 students with varied marks, categories,
application dates, and 1-3 ranked preferences each.

Usage:
    cd backend
    PYTHONPATH=. python ../sample_data/seed_sample_data.py
"""
import asyncio
import random
from datetime import date, timedelta

from app.core.db import AsyncSessionLocal
from app.models.allocation import CoursePreference
from app.models.course import Course, CourseSeatReservation
from app.models.enums import CategoryEnum
from app.models.student import Student

random.seed(42)

COURSES = [
    ("Computer Science Engineering", "CSE", 40, {"OBC": 8, "SC": 5, "ST": 3}),
    ("Electronics & Communication", "ECE", 35, {"OBC": 7, "SC": 4, "ST": 2}),
    ("Mechanical Engineering", "MECH", 30, {"OBC": 6, "SC": 4, "ST": 2}),
    ("Civil Engineering", "CIVIL", 25, {"OBC": 5, "SC": 3, "ST": 2}),
    ("Information Technology", "IT", 30, {"OBC": 6, "SC": 3, "ST": 2}),
    ("Electrical Engineering", "EEE", 25, {"OBC": 5, "SC": 3, "ST": 1}),
    ("Biotechnology", "BT", 20, {"OBC": 4, "SC": 2, "ST": 1}),
    ("Data Science", "DS", 20, {"OBC": 4, "SC": 2, "ST": 1}),
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Ananya", "Diya", "Saanvi", "Aadhya", "Kavya", "Myra", "Anika", "Riya", "Ira", "Sara",
    "Karthik", "Naveen", "Deepak", "Rahul", "Vikram", "Priya", "Sneha", "Divya", "Meera", "Pooja",
]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Nair", "Reddy", "Menon", "Rao", "Pillai", "Gupta", "Kumar"]

CATEGORY_WEIGHTS = [(CategoryEnum.GENERAL, 0.5), (CategoryEnum.OBC, 0.27), (CategoryEnum.SC, 0.15), (CategoryEnum.ST, 0.08)]


def weighted_category() -> CategoryEnum:
    r = random.random()
    cumulative = 0.0
    for cat, weight in CATEGORY_WEIGHTS:
        cumulative += weight
        if r <= cumulative:
            return cat
    return CategoryEnum.GENERAL


async def seed():
    async with AsyncSessionLocal() as db:
        print("Seeding courses...")
        course_objs = []
        for name, code, total_seats, reservations in COURSES:
            course = Course(name=name, code=code, total_seats=total_seats)
            db.add(course)
            await db.flush()
            for cat_str, seats in reservations.items():
                db.add(CourseSeatReservation(course_id=course.id, category=CategoryEnum[cat_str], reserved_seats=seats))
            course_objs.append(course)
        await db.commit()

        print(f"Seeding 60 students...")
        base_date = date(2026, 1, 1)
        for i in range(60):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            email = f"{name.lower().replace(' ', '.')}{i}@example.edu"
            marks = round(random.uniform(45, 99), 2)
            category = weighted_category()
            application_date = base_date + timedelta(days=random.randint(0, 45))

            student = Student(
                student_code=f"STU-2026-{i + 1:04d}",
                name=name,
                email=email,
                marks=marks,
                category=category,
                application_date=application_date,
            )
            db.add(student)
            await db.flush()

            # 1-3 distinct random preferences, weighted toward popular courses (CSE/IT/DS)
            num_prefs = random.randint(1, 3)
            weighted_courses = course_objs + [course_objs[0], course_objs[4], course_objs[7]]  # bias CSE/IT/DS
            chosen = random.sample(list({c.id: c for c in weighted_courses}.values()), k=min(num_prefs, len(course_objs)))
            for priority, course in enumerate(chosen, start=1):
                db.add(CoursePreference(student_id=student.id, course_id=course.id, priority=priority))

        await db.commit()
        print("Done. Seeded 8 courses and 60 students.")
        print("Run POST /api/v1/allocation/run to allocate them.")


if __name__ == "__main__":
    asyncio.run(seed())
