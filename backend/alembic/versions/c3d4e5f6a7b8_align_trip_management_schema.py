"""Align the trip table with the Milestone 2 trip workflow.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-14
"""
from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE trip_status RENAME VALUE 'In Transit' TO 'Active'")
    op.alter_column("trips", "start_location", new_column_name="source")
    op.alter_column("trips", "start_time", new_column_name="started_at")
    op.alter_column("trips", "end_time", new_column_name="ended_at")
    op.alter_column("trips", "distance_meters", new_column_name="planned_distance")
    op.alter_column("trips", "duration_seconds", new_column_name="estimated_duration")


def downgrade() -> None:
    op.alter_column("trips", "estimated_duration", new_column_name="duration_seconds")
    op.alter_column("trips", "planned_distance", new_column_name="distance_meters")
    op.alter_column("trips", "ended_at", new_column_name="end_time")
    op.alter_column("trips", "started_at", new_column_name="start_time")
    op.alter_column("trips", "source", new_column_name="start_location")
    op.execute("ALTER TYPE trip_status RENAME VALUE 'Active' TO 'In Transit'")
