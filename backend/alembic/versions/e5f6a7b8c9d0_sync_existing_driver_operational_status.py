"""synchronize existing driver operational status

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE drivers SET status = (CASE "
        "WHEN EXISTS (SELECT 1 FROM trips WHERE trips.driver_id = drivers.driver_id AND trips.status = 'Active') THEN 'On Trip' "
        "WHEN EXISTS (SELECT 1 FROM trips WHERE trips.driver_id = drivers.driver_id AND trips.status = 'Scheduled') THEN 'Offline' "
        "ELSE 'Available' END)::driver_status "
        "WHERE status = 'Available'::driver_status"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE drivers SET status = 'Available'::driver_status "
        "WHERE status IN ('On Trip'::driver_status, 'Offline'::driver_status) "
        "AND EXISTS (SELECT 1 FROM trips WHERE trips.driver_id = drivers.driver_id AND trips.status IN ('Scheduled', 'Active'))"
    )
