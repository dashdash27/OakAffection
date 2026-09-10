"""add_new_delivery_service_to_enum

Revision ID: 4b3d2c4b14a3
Revises: d83876f035b3
Create Date: 2026-09-10 16:22:30.301548

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b3d2c4b14a3'
down_revision = 'd83876f035b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Отключаем транзакцию для Postgres, чтобы добавить значение в ENUM
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE deliveryservice ADD VALUE 'ozon'")

def downgrade() -> None:
    # Откат не требуется, оставляем пустым
    pass
