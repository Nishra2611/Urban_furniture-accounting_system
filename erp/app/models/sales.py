from decimal import Decimal
from typing import Optional
from datetime import date as date_type

from sqlalchemy import (
    String, Integer, Numeric, Date, ForeignKey, Text,
    Enum as SAEnum, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin
from app.models.enums import DocumentStatus, PaymentStatus


class SalesOrder(Base, TimestampMixin):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    order_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    lines: Mapped[list["SalesOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    order: Mapped["SalesOrder"] = relationship(back_populates="lines")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_so_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_so_line_price_nonneg"),
        CheckConstraint("tax_rate >= 0", name="ck_so_line_tax_nonneg"),
    )


class SaleInvoice(Base, TimestampMixin):
    __tablename__ = "sale_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    sales_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_orders.id"), nullable=True)
    invoice_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    lines: Mapped[list["SaleInvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Prevent the same confirmed Sales Order from being converted into more than one invoice.
        UniqueConstraint("sales_order_id", name="uq_invoice_per_sales_order"),
    )


class SaleInvoiceLine(Base):
    __tablename__ = "sale_invoice_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("sale_invoices.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    invoice: Mapped["SaleInvoice"] = relationship(back_populates="lines")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_si_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_si_line_price_nonneg"),
        CheckConstraint("tax_rate >= 0", name="ck_si_line_tax_nonneg"),
    )


class Receipt(Base, TimestampMixin):
    """Money received from a customer against a Sale Invoice."""
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    sale_invoice_id: Mapped[int] = mapped_column(ForeignKey("sale_invoices.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    receipt_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.CONFIRMED, nullable=False
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(80), unique=True, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_receipt_amount_positive"),
    )
