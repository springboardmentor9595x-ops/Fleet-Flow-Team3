"""Finalize shipment and trip schema for Milestone 2.

Revision ID: b2c3d4e5f6a7
Revises: 346bec11a95b
Create Date: 2026-08-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "346bec11a95b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


shipment_status = postgresql.ENUM(
    "Created", "Assigned", "In Transit", "Delayed", "Delivered", "Cancelled",
    name="shipment_status",
)
trip_status = postgresql.ENUM(
    "Scheduled", "In Transit", "Completed", "Cancelled", name="trip_status",
)


def upgrade() -> None:
    shipment_status.create(op.get_bind(), checkfirst=True)
    trip_status.create(op.get_bind(), checkfirst=True)

    op.alter_column("shipments", "status", server_default=None)
    op.alter_column(
        "shipments", "status", existing_type=sa.String(length=30),
        type_=shipment_status, postgresql_using="status::shipment_status",
        existing_nullable=False,
    )
    op.alter_column("shipments", "status", server_default="Created")
    op.add_column("trips", sa.Column("start_location", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("trips", sa.Column("destination", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("trips", sa.Column("start_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trips", sa.Column("end_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trips", sa.Column("distance_meters", sa.Float(), nullable=True))
    op.add_column("trips", sa.Column("duration_seconds", sa.Float(), nullable=True))
    op.add_column("trips", sa.Column("actual_distance_meters", sa.Float(), nullable=True))
    op.add_column("trips", sa.Column("status", trip_status, nullable=False, server_default="Scheduled"))
    op.add_column("trips", sa.Column("route_type", sa.String(length=30), nullable=False, server_default="Fastest"))
    op.add_column("trips", sa.Column("route_geometry", sa.JSON(), nullable=True))
    op.add_column("trips", sa.Column("eta", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trips", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.alter_column("trips", "start_location", server_default=None)
    op.alter_column("trips", "destination", server_default=None)
    op.alter_column("trips", "status", server_default=None)
    op.alter_column("trips", "route_type", server_default=None)
    op.alter_column("trips", "created_at", server_default=None)


def downgrade() -> None:
    op.drop_column("trips", "created_at")
    op.drop_column("trips", "eta")
    op.drop_column("trips", "route_geometry")
    op.drop_column("trips", "route_type")
    op.drop_column("trips", "status")
    op.drop_column("trips", "actual_distance_meters")
    op.drop_column("trips", "duration_seconds")
    op.drop_column("trips", "distance_meters")
    op.drop_column("trips", "end_time")
    op.drop_column("trips", "start_time")
    op.drop_column("trips", "destination")
    op.drop_column("trips", "start_location")
    op.alter_column("shipments", "status", server_default=None)
    op.alter_column(
        "shipments", "status", existing_type=shipment_status,
        type_=sa.String(length=30), postgresql_using="status::text",
        existing_nullable=False,
    )
    op.alter_column("shipments", "status", server_default="Created")
    trip_status.drop(op.get_bind(), checkfirst=True)
    shipment_status.drop(op.get_bind(), checkfirst=True)
