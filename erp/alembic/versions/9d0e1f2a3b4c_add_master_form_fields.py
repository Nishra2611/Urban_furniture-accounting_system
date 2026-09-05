"""persist visible master form fields

Revision ID: 9d0e1f2a3b4c
Revises: 8c9d0e1f2a3b
Create Date: 2026-09-05

"""
from alembic import op
import sqlalchemy as sa


revision = "9d0e1f2a3b4c"
down_revision = "8c9d0e1f2a3b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("contacts", sa.Column("tax_id", sa.String(length=60), nullable=True))
    op.add_column("contacts", sa.Column("image_url", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("product_type", sa.String(length=20), nullable=False, server_default="Goods"))
    op.add_column("products", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("image_url", sa.Text(), nullable=True))
    op.add_column("analytic_accounts", sa.Column("type", sa.String(length=20), nullable=False, server_default="Expense"))
    op.add_column("analytic_budgets", sa.Column("responsible_name", sa.String(length=150), nullable=True))
    op.add_column("analytic_budgets", sa.Column("stage", sa.String(length=20), nullable=False, server_default="Draft"))
    op.add_column("analytic_budgets", sa.Column("revised_with", sa.String(length=200), nullable=True))
    op.add_column("analytic_budgets", sa.Column("revision_of", sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column("analytic_budgets", "revision_of")
    op.drop_column("analytic_budgets", "revised_with")
    op.drop_column("analytic_budgets", "stage")
    op.drop_column("analytic_budgets", "responsible_name")
    op.drop_column("analytic_accounts", "type")
    op.drop_column("products", "image_url")
    op.drop_column("products", "category")
    op.drop_column("products", "product_type")
    op.drop_column("contacts", "image_url")
    op.drop_column("contacts", "tax_id")