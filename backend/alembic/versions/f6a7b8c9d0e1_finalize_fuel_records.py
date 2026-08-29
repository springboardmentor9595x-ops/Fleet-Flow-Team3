"""finalize fuel records for fuel monitoring analytics

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable preserves any legacy stub rows. New API-created records require
    # all four values through their Pydantic request schema.
    op.add_column("fuel_records", sa.Column("fuel_amount", sa.Numeric(12, 3), nullable=True))
    op.add_column("fuel_records", sa.Column("fuel_cost", sa.Numeric(12, 2), nullable=True))
    op.add_column("fuel_records", sa.Column("mileage", sa.Numeric(12, 2), nullable=True))
    op.add_column("fuel_records", sa.Column("refill_date", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_fuel_records_vehicle_refill_date",
        "fuel_records",
        ["vehicle_id", "refill_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_fuel_records_vehicle_refill_date", table_name="fuel_records")
    op.drop_column("fuel_records", "refill_date")
    op.drop_column("fuel_records", "mileage")
    op.drop_column("fuel_records", "fuel_cost")
    op.drop_column("fuel_records", "fuel_amount")
