"""convert users role to enum

Revision ID: c1d6aedd10fa
Revises: e997350ce276
Create Date: 2026-08-08 15:31:38.461933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1d6aedd10fa'
down_revision: Union[str, Sequence[str], None] = 'e997350ce276'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM(
        "Admin",
        "FleetManager",
        "Driver",
        "Dispatcher",
        name="user_role",
    )

    user_role.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=30),
        type_=user_role,
        postgresql_using="role::user_role",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "role",
        existing_type=postgresql.ENUM(
            "Admin",
            "FleetManager",
            "Driver",
            "Dispatcher",
            name="user_role",
        ),
        type_=sa.String(length=30),
        postgresql_using="role::text",
        existing_nullable=False,
    )

    postgresql.ENUM(name="user_role").drop(
        op.get_bind(),
        checkfirst=True,
    )