from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, ActiveMixin
from app.models.enums import PartyType, AccountType


class Contact(Base, TimestampMixin, ActiveMixin):
    """Customer / Vendor master record."""
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    party_type: Mapped[PartyType] = mapped_column(SAEnum(PartyType), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Linked receivable/payable account for this party, used when posting accounting entries.
    receivable_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chart_of_accounts.id"), nullable=True
    )
    payable_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chart_of_accounts.id"), nullable=True
    )


class Product(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(20), default="Goods", nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sales_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    track_stock: Mapped[bool] = mapped_column(default=False, nullable=False)
    stock_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0, nullable=False)

    # Default income/expense accounts used when posting invoice/bill lines for this product.
    income_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chart_of_accounts.id"), nullable=True
    )
    expense_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chart_of_accounts.id"), nullable=True
    )


class Tax(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "taxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)


class ChartOfAccount(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "chart_of_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(SAEnum(AccountType), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chart_of_accounts.id"), nullable=True)


class AnalyticAccount(Base, TimestampMixin, ActiveMixin):
    """Analytical/cost-center dimension, independent of the Chart of Accounts."""
    __tablename__ = "analytic_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="Expense", nullable=False)


class AnalyticBudget(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "analytic_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    analytic_account_id: Mapped[int] = mapped_column(
        ForeignKey("analytic_accounts.id"), nullable=False
    )
    period_start: Mapped[str] = mapped_column(String(10), nullable=False)  # ISO date
    period_end: Mapped[str] = mapped_column(String(10), nullable=False)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    responsible_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    stage: Mapped[str] = mapped_column(String(20), default="Draft", nullable=False)
    revised_with: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    revision_of: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    # Achieved/Committed are derived at report time from actual transactions,
    # not stored as separately-editable fields.
