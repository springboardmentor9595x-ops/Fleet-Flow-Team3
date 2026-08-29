"""initial schema

Revision ID: ff3dac1495e8
Revises: 
Create Date: 2026-07-24 17:09:17.653298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff3dac1495e8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the foundational User, Vehicle, and Driver tables."""
    op.create_table(
        "users",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=True),
        # Converted to the PostgreSQL user_role enum by a later revision.
        sa.Column("role", sa.String(length=30), nullable=False, server_default="Driver"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email", name="users_email_key"),
    )
    op.create_table('vehicles',
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('vehicle_id')
    )
    op.create_table('drivers',
    sa.Column('driver_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('driver_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('drivers')
    op.drop_table('vehicles')
    op.drop_table("users")
