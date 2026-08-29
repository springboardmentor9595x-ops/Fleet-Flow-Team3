"""add fuel display references and resolved maintenance status

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("fuel_records", sa.Column("fuel_reference", sa.String(length=20), nullable=True))
    op.execute(
        """
        WITH numbered AS (
            SELECT fuel_id, ROW_NUMBER() OVER (ORDER BY fuel_id) AS sequence
            FROM fuel_records
        )
        UPDATE fuel_records AS fuel
        SET fuel_reference = 'FUEL-' || LPAD(numbered.sequence::text, 4, '0')
        FROM numbered
        WHERE fuel.fuel_id = numbered.fuel_id
        """
    )
    op.create_index("ix_fuel_records_fuel_reference", "fuel_records", ["fuel_reference"], unique=True)
    # PostgreSQL cannot remove enum values safely during downgrade. The
    # additive enum value is deliberately retained during a downgrade.
    op.execute("ALTER TYPE maintenance_status ADD VALUE IF NOT EXISTS 'Resolved'")


def downgrade() -> None:
    op.drop_index("ix_fuel_records_fuel_reference", table_name="fuel_records")
    op.drop_column("fuel_records", "fuel_reference")
