"""create maintenance table

Revision ID: 6ddbd6eb69ed
Revises: c3d4e5f6a7b8
Create Date: 2026-08-21 18:28:46.682914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6ddbd6eb69ed'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    maintenance_status = sa.Enum(
        "Scheduled",
        "In Progress",
        "Completed",
        "Cancelled",
        name="maintenance_status",
    )

    op.create_table(
        "maintenance",
        sa.Column(
            "maintenance_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            maintenance_status,
            nullable=False,
            server_default=sa.text("'Scheduled'"),
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completion_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "upcoming_alert_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "overdue_alert_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.vehicle_id"],
        ),
        sa.PrimaryKeyConstraint("maintenance_id"),
    )

    op.create_index(
        "ix_maintenance_vehicle_id",
        "maintenance",
        ["vehicle_id"],
        unique=False,
    )

    op.create_index(
        "ix_maintenance_scheduled_at",
        "maintenance",
        ["scheduled_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_scheduled_at",
        table_name="maintenance",
    )

    op.drop_index(
        "ix_maintenance_vehicle_id",
        table_name="maintenance",
    )

    op.drop_table("maintenance")

    maintenance_status = sa.Enum(
        "Scheduled",
        "In Progress",
        "Completed",
        "Cancelled",
        name="maintenance_status",
    )

    maintenance_status.drop(op.get_bind(), checkfirst=True)
