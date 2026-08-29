"""add email verification fields

Revision ID: a1b2c3d4e5f6
Revises: f0bc9e273a1f
Create Date: 2026-08-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f0bc9e273a1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("users", sa.Column("verification_code_hash", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("verification_code_expires_at", sa.DateTime(), nullable=True))
    # Accounts created before this feature remain able to log in.
    op.execute("UPDATE users SET email_verified = true")
    op.alter_column("users", "email_verified", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "verification_code_expires_at")
    op.drop_column("users", "verification_code_hash")
    op.drop_column("users", "email_verified")
