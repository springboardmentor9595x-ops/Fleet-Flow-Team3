"""add stub table foreign keys

Revision ID: f0bc9e273a1f
Revises: c1d6aedd10fa
Create Date: 2026-08-08 18:04:20.539691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f0bc9e273a1f'
down_revision: Union[str, Sequence[str], None] = 'c1d6aedd10fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_drivers_user_id",
        "drivers",
        ["user_id"],
    )

    op.create_foreign_key(
        "fk_vehicles_assigned_driver",
        "vehicles",
        "drivers",
        ["assigned_driver"],
        ["driver_id"],
    )

    op.add_column(
        "shipments",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "shipments",
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_shipments_vehicle_id",
        "shipments",
        "vehicles",
        ["vehicle_id"],
        ["vehicle_id"],
    )
    op.create_foreign_key(
        "fk_shipments_driver_id",
        "shipments",
        "drivers",
        ["driver_id"],
        ["driver_id"],
    )

    op.add_column(
        "trips",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "trips",
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "trips",
        sa.Column("shipment_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_trips_vehicle_id",
        "trips",
        "vehicles",
        ["vehicle_id"],
        ["vehicle_id"],
    )
    op.create_foreign_key(
        "fk_trips_driver_id",
        "trips",
        "drivers",
        ["driver_id"],
        ["driver_id"],
    )
    op.create_foreign_key(
        "fk_trips_shipment_id",
        "trips",
        "shipments",
        ["shipment_id"],
        ["shipment_id"],
    )

    op.add_column(
        "gps_tracking",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_gps_tracking_vehicle_id",
        "gps_tracking",
        "vehicles",
        ["vehicle_id"],
        ["vehicle_id"],
    )

    op.add_column(
        "vehicle_maintenance",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_vehicle_maintenance_vehicle_id",
        "vehicle_maintenance",
        "vehicles",
        ["vehicle_id"],
        ["vehicle_id"],
    )

    op.add_column(
        "fuel_records",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_fuel_records_vehicle_id",
        "fuel_records",
        "vehicles",
        ["vehicle_id"],
        ["vehicle_id"],
    )

    op.add_column(
        "notifications",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_notifications_user_id",
        "notifications",
        "users",
        ["user_id"],
        ["user_id"],
    )

    op.add_column(
        "attendance",
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_attendance_driver_id",
        "attendance",
        "drivers",
        ["driver_id"],
        ["driver_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_attendance_driver_id", "attendance", type_="foreignkey")
    op.drop_column("attendance", "driver_id")

    op.drop_constraint("fk_notifications_user_id", "notifications", type_="foreignkey")
    op.drop_column("notifications", "user_id")

    op.drop_constraint("fk_fuel_records_vehicle_id", "fuel_records", type_="foreignkey")
    op.drop_column("fuel_records", "vehicle_id")

    op.drop_constraint(
        "fk_vehicle_maintenance_vehicle_id",
        "vehicle_maintenance",
        type_="foreignkey",
    )
    op.drop_column("vehicle_maintenance", "vehicle_id")

    op.drop_constraint(
        "fk_gps_tracking_vehicle_id",
        "gps_tracking",
        type_="foreignkey",
    )
    op.drop_column("gps_tracking", "vehicle_id")

    op.drop_constraint("fk_trips_shipment_id", "trips", type_="foreignkey")
    op.drop_constraint("fk_trips_driver_id", "trips", type_="foreignkey")
    op.drop_constraint("fk_trips_vehicle_id", "trips", type_="foreignkey")
    op.drop_column("trips", "shipment_id")
    op.drop_column("trips", "driver_id")
    op.drop_column("trips", "vehicle_id")

    op.drop_constraint("fk_shipments_driver_id", "shipments", type_="foreignkey")
    op.drop_constraint("fk_shipments_vehicle_id", "shipments", type_="foreignkey")
    op.drop_column("shipments", "driver_id")
    op.drop_column("shipments", "vehicle_id")

    op.drop_constraint(
        "fk_vehicles_assigned_driver",
        "vehicles",
        type_="foreignkey",
    )

    op.drop_constraint("uq_drivers_user_id", "drivers", type_="unique")
