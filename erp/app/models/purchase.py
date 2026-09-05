from decimal import Decimal
from typing import Optional
from datetime import date as date_type

from sqlalchemy import (
    String, Integer, Numeric, Date, ForeignKey,
    Enum as SAEnum, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin
from app.models.enums import DocumentStatus, PaymentStatus


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    order_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    order: Mapped["PurchaseOrder"] = relationship(back_populates="lines")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_po_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_po_line_price_nonneg"),
        CheckConstraint("tax_rate >= 0", name="ck_po_line_tax_nonneg"),
    )


class PurchaseBill(Base, TimestampMixin):
    __tablename__ = "purchase_bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bill_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    bill_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    lines: Mapped[list["PurchaseBillLine"]] = relationship(
        back_populates="bill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("purchase_order_id", name="uq_bill_per_purchase_order"),
    )


class PurchaseBillLine(Base):
    __tablename__ = "purchase_bill_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("purchase_bills.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    bill: Mapped["PurchaseBill"] = relationship(back_populates="lines")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_pb_line_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_pb_line_price_nonneg"),
        CheckConstraint("tax_rate >= 0", name="ck_pb_line_tax_nonneg"),
    )


class VendorPayment(Base, TimestampMixin):
    """Money paid to a vendor against a Purchase Bill."""
    __tablename__ = "vendor_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    purchase_bill_id: Mapped[int] = mapped_column(ForeignKey("purchase_bills.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.CONFIRMED, nullable=False
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(80), unique=True, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_vendor_payment_amount_positive"),
    )
