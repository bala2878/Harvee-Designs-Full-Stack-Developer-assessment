from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("table_name", sa.String(63), nullable=False),
        sa.Column("row_count", sa.Integer, server_default="0"),
        sa.Column("columns_metadata", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("table_name", name="uq_datasets_table_name"),
    )

    op.create_table(
        "query_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("question", sa.String(1000), nullable=False),
        sa.Column("generated_sql", sa.String(4000), nullable=False),
        sa.Column("row_count_returned", sa.Integer, nullable=True),
        sa.Column("success", sa.Boolean, server_default=sa.true()),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("execution_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_query_history_dataset_id", "query_history", ["dataset_id"])
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sqlassistant_readonly') THEN
                CREATE ROLE sqlassistant_readonly WITH LOGIN PASSWORD 'sqlassistant_readonly_pass';
            END IF;
        END
        $$;
        """
    )
    op.execute("CREATE SCHEMA IF NOT EXISTS datasets")
    op.execute("GRANT USAGE ON SCHEMA datasets TO sqlassistant_readonly")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA datasets GRANT SELECT ON TABLES TO sqlassistant_readonly")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA datasets TO sqlassistant_readonly")
    op.execute("REVOKE ALL ON SCHEMA public FROM sqlassistant_readonly")


def downgrade() -> None:
    op.drop_index("ix_query_history_dataset_id", table_name="query_history")
    op.drop_table("query_history")
    op.drop_table("datasets")
    op.execute("REVOKE ALL ON SCHEMA datasets FROM sqlassistant_readonly")
