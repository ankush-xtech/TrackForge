"""add created_by to users

Revision ID: a2f8b3c4d5e6
Revises: 881a741d793d
Create Date: 2026-04-06 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a2f8b3c4d5e6'
down_revision: Union[str, None] = '881a741d793d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_by column — nullable because self-registered org admins won't have a creator
    op.add_column('users', sa.Column('created_by', UUID(as_uuid=True), nullable=True))

    # Add foreign key to users.id (self-referencing)
    op.create_foreign_key(
        'fk_users_created_by',
        'users', 'users',
        ['created_by'], ['id'],
    )

    # Index for fast lookups: "show me all users I created"
    op.create_index('ix_users_created_by', 'users', ['created_by'])


def downgrade() -> None:
    op.drop_index('ix_users_created_by', table_name='users')
    op.drop_constraint('fk_users_created_by', 'users', type_='foreignkey')
    op.drop_column('users', 'created_by')
