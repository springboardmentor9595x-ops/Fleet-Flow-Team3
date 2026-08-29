"""complete driver assignment profiles and activity

Revision ID: d4e5f6a7b8c9
Revises: 517d09fc6362
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "517d09fc6362"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


driver_status = postgresql.ENUM(
    "Available", "On Trip", "Offline", "Inactive", name="driver_status", create_type=False
)
attendance_activity_type = postgresql.ENUM(
    "Trip Started",
    "Trip Completed",
    "Attendance / Check-in",
    "Attendance / Check-out",
    name="attendance_activity_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE driver_status AS ENUM "
        "('Available', 'On Trip', 'Offline', 'Inactive')"
    )
    op.add_column("drivers", sa.Column("license_number", sa.String(length=50), nullable=True))
    op.add_column(
        "drivers",
        sa.Column("experience_years", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("drivers", sa.Column("address", sa.String(length=255), nullable=True))
    op.add_column(
        "drivers",
        sa.Column("status", driver_status, nullable=False, server_default="Available"),
    )
    op.create_unique_constraint("uq_drivers_license_number", "drivers", ["license_number"])
    op.create_index("ix_drivers_status", "drivers", ["status"])

    op.execute(
        "CREATE TYPE attendance_activity_type AS ENUM "
        "('Trip Started', 'Trip Completed', 'Attendance / Check-in', 'Attendance / Check-out')"
    )
    op.add_column(
        "attendance",
        sa.Column(
            "activity_type",
            attendance_activity_type,
            nullable=False,
            server_default="Attendance / Check-in",
        ),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column("attendance", sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("attendance", sa.Column("notes", sa.String(length=500), nullable=True))
    op.create_foreign_key("fk_attendance_trip_id", "attendance", "trips", ["trip_id"], ["trip_id"])
    op.create_index("ix_attendance_driver_occurred_at", "attendance", ["driver_id", "occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_attendance_driver_occurred_at", table_name="attendance")
    op.drop_constraint("fk_attendance_trip_id", "attendance", type_="foreignkey")
    op.drop_column("attendance", "notes")
    op.drop_column("attendance", "trip_id")
    op.drop_column("attendance", "occurred_at")
    op.drop_column("attendance", "activity_type")
    op.execute("DROP TYPE attendance_activity_type")

    op.drop_index("ix_drivers_status", table_name="drivers")
    op.drop_constraint("uq_drivers_license_number", "drivers", type_="unique")
    op.drop_column("drivers", "status")
    op.drop_column("drivers", "address")
    op.drop_column("drivers", "experience_years")
    op.drop_column("drivers", "license_number")
    op.execute("DROP TYPE driver_status")
