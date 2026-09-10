"""add_new_delivery_service_to_enum

Revision ID: 6d0b976c10e4
Revises: d83876f035b3
Create Date: 2026-09-10 16:53:54.409174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d0b976c10e4'
down_revision = 'd83876f035b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        # Добавляем ТОЛЬКО заглавный вариант, так как вся база на верхнем регистре
        op.execute("ALTER TYPE deliveryservice ADD VALUE IF NOT EXISTS 'OZON'")


def downgrade():
    pass
