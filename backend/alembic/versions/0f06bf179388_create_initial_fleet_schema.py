"""Create initial fleet schema

Revision ID: 0f06bf179388
Revises: ff3dac1495e8
Create Date: 2026-08-06 21:17:14.434123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = "0f06bf179388"
down_revision: Union[str, Sequence[str], None] = "ff3dac1495e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attendance",
        sa.Column("attendance_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("attendance_id"),
    )

    op.create_table(
        "fuel_records",
        sa.Column("fuel_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("fuel_id"),
    )

    op.create_table(
        "gps_tracking",
        sa.Column("gps_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("gps_id"),
    )

    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("notification_id"),
    )

    op.create_table(
        "shipments",
        sa.Column("shipment_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("shipment_id"),
    )

    op.create_table(
        "trips",
        sa.Column("trip_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("trip_id"),
    )

    op.create_table(
        "vehicle_maintenance",
        sa.Column("maintenance_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("maintenance_id"),
    )

    op.add_column(
        "drivers",
        sa.Column("full_name", sa.String(length=100), nullable=True),
    )



def downgrade() -> None:
    op.drop_column("drivers", "full_name")
    op.drop_table("vehicle_maintenance")
    op.drop_table("trips")
    op.drop_table("shipments")
    op.drop_table("notifications")
    op.drop_table("gps_tracking")
    op.drop_table("fuel_records")
    op.drop_table("attendance")
