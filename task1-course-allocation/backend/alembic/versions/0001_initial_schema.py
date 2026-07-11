from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


category_enum = postgresql.ENUM("GENERAL", "OBC", "SC", "ST", name="category_enum")
allocation_status_enum = postgresql.ENUM("ALLOCATED", "NOT_ALLOCATED", name="allocation_status_enum")
allocation_run_status_enum = postgresql.ENUM(
    "PENDING", "RUNNING", "COMPLETED", "FAILED", name="allocation_run_status_enum"
)


def upgrade() -> None:
    bind = op.get_bind()
    category_enum.create(bind, checkfirst=True)
    allocation_status_enum.create(bind, checkfirst=True)
    allocation_run_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("marks", sa.Float, nullable=False),
        sa.Column(
            "category", postgresql.ENUM(name="category_enum", create_type=False), nullable=False
        ),
        sa.Column("application_date", sa.Date, nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("student_code", name="uq_students_student_code"),
        sa.UniqueConstraint("email", name="uq_students_email"),
    )
    op.create_index("ix_students_marks_desc", "students", ["marks", "application_date"])

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("total_seats", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_courses_name"),
        sa.UniqueConstraint("code", name="uq_courses_code"),
    )

    op.create_table(
        "course_seat_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category", postgresql.ENUM(name="category_enum", create_type=False), nullable=False
        ),
        sa.Column("reserved_seats", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("course_id", "category", name="uq_course_category"),
    )

    op.create_table(
        "course_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.UniqueConstraint("student_id", "priority", name="uq_student_priority"),
        sa.UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )

    op.create_table(
        "allocation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="allocation_run_status_enum", create_type=False),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("total_students", sa.Integer, server_default="0"),
        sa.Column("total_allocated", sa.Integer, server_default="0"),
        sa.Column("total_unallocated", sa.Integer, server_default="0"),
        sa.Column("triggered_by", sa.String(150), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "allocation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("allocation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status", postgresql.ENUM(name="allocation_status_enum", create_type=False), nullable=False
        ),
        sa.Column("preference_rank_matched", sa.Integer, nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("student_id", name="uq_allocations_student_id"),
    )


def downgrade() -> None:
    op.drop_table("allocations")
    op.drop_table("allocation_runs")
    op.drop_table("course_preferences")
    op.drop_table("course_seat_reservations")
    op.drop_table("courses")
    op.drop_index("ix_students_marks_desc", table_name="students")
    op.drop_table("students")

    bind = op.get_bind()
    allocation_run_status_enum.drop(bind, checkfirst=True)
    allocation_status_enum.drop(bind, checkfirst=True)
    category_enum.drop(bind, checkfirst=True)
