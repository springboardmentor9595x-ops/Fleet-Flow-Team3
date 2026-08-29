"""finalize shipments table

Revision ID: 7cd5cfb0709d
Revises: a1b2c3d4e5f6
Create Date: 2026-08-09 14:51:43.186094

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7cd5cfb0709d"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "shipments",
        sa.Column(
            "tracking_number",
            sa.String(length=50),
            nullable=False,
        ),
    )

    op.add_column(
        "shipments",
        sa.Column(
            "source",
            sa.String(length=255),
            nullable=False,
        ),
    )

    op.add_column(
        "shipments",
        sa.Column(
            "destination",
            sa.String(length=255),
            nullable=False,
        ),
    )

    op.add_column(
        "shipments",
        sa.Column(
            "customer_name",
            sa.String(length=255),
            nullable=False,
        ),
    )

    op.add_column(
        "shipments",
        sa.Column(
            "shipment_weight",
            sa.Float(),
            nullable=False,
        ),
    )

    op.add_column(
        "shipments",
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="Created",
        ),
    )

    op.add_column(
        "shipments",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        op.f("ix_shipments_tracking_number"),
        "shipments",
        ["tracking_number"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_shipments_tracking_number"),
        table_name="shipments",
    )

    op.drop_column("shipments", "created_at")
    op.drop_column("shipments", "status")
    op.drop_column("shipments", "shipment_weight")
    op.drop_column("shipments", "customer_name")
    op.drop_column("shipments", "destination")
    op.drop_column("shipments", "source")
    op.drop_column("shipments", "tracking_number")