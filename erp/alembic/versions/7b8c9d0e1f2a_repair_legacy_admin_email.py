"""repair legacy admin email

Revision ID: 7b8c9d0e1f2a
Revises: 26d03d48dedf
Create Date: 2026-09-05

"""
from alembic import op
import sqlalchemy as sa


revision = "7b8c9d0e1f2a"
down_revision = "26d03d48dedf"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text(
            "UPDATE users "
            "SET email = 'admin@urbanfurniture.com' "
            "WHERE login_id = 'admin01' AND email = 'admin@urbanfurniture.local'"
        )
    )


def downgrade():
    op.execute(
        sa.text(
            "UPDATE users "
            "SET email = 'admin@urbanfurniture.local' "
            "WHERE login_id = 'admin01' AND email = 'admin@urbanfurniture.com'"
        )
    )