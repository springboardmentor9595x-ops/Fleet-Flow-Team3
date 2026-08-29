"""finalize maintenance scheduling and notifications

Revision ID: 517d09fc6362
Revises: 6ddbd6eb69ed
Create Date: 2026-08-21 18:46:56.408199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '517d09fc6362'
down_revision: Union[str, Sequence[str], None] = '6ddbd6eb69ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("maintenance", "title", new_column_name="maintenance_type")
    op.alter_column("maintenance", "description", new_column_name="remarks")
    op.alter_column("maintenance", "scheduled_at", new_column_name="service_date")
    op.execute("ALTER INDEX ix_maintenance_scheduled_at RENAME TO ix_maintenance_service_date")
    op.execute("ALTER TYPE maintenance_status RENAME VALUE 'In Progress' TO 'InProgress'")
    op.add_column("maintenance", sa.Column("next_service_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("maintenance", sa.Column("cost", sa.Numeric(12, 2), nullable=True))
    op.create_index("ix_maintenance_next_service_date", "maintenance", ["next_service_date"], unique=False)

    op.add_column("notifications", sa.Column("maintenance_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("notifications", sa.Column("alert_type", sa.String(length=30), nullable=True))
    op.add_column("notifications", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notifications", sa.Column("delivered", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_foreign_key("fk_notifications_maintenance_id", "notifications", "maintenance", ["maintenance_id"], ["maintenance_id"])
    op.create_index("ix_notifications_maintenance_id", "notifications", ["maintenance_id"], unique=False)
    op.create_unique_constraint("uq_notifications_maintenance_alert_type", "notifications", ["maintenance_id", "alert_type"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_notifications_maintenance_alert_type", "notifications", type_="unique")
    op.drop_index("ix_notifications_maintenance_id", table_name="notifications")
    op.drop_constraint("fk_notifications_maintenance_id", "notifications", type_="foreignkey")
    op.drop_column("notifications", "delivered")
    op.drop_column("notifications", "sent_at")
    op.drop_column("notifications", "alert_type")
    op.drop_column("notifications", "maintenance_id")
    op.drop_index("ix_maintenance_next_service_date", table_name="maintenance")
    op.drop_column("maintenance", "cost")
    op.drop_column("maintenance", "next_service_date")
    op.execute("ALTER TYPE maintenance_status RENAME VALUE 'InProgress' TO 'In Progress'")
    op.execute("ALTER INDEX ix_maintenance_service_date RENAME TO ix_maintenance_scheduled_at")
    op.alter_column("maintenance", "service_date", new_column_name="scheduled_at")
    op.alter_column("maintenance", "remarks", new_column_name="description")
    op.alter_column("maintenance", "maintenance_type", new_column_name="title")
