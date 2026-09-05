from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class LineItemCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Optional[Decimal] = None  # falls back to product's price if omitted
    tax_rate: Optional[Decimal] = None    # falls back to product's tax rate if omitted


class SalesOrderCreate(BaseModel):
    contact_id: int
    order_date: str
    lines: list[LineItemCreate]


class SalesOrderOut(BaseModel):
    id: int
    order_number: str
    contact_id: int
    order_date: str
    status: str
    total_amount: Decimal

    class Config:
        from_attributes = True


class SaleInvoiceCreate(BaseModel):
    contact_id: int
    invoice_date: str
    sales_order_id: Optional[int] = None
    lines: list[LineItemCreate] = []  # can be empty only if converting from a sales order


class SaleInvoiceOut(BaseModel):
    id: int
    invoice_number: str
    contact_id: int
    invoice_date: str
    status: str
    payment_status: str
    total_amount: Decimal
    amount_paid: Decimal

    class Config:
        from_attributes = True


class ReceiptCreate(BaseModel):
    sale_invoice_id: int
    amount: Decimal
    receipt_date: str
    idempotency_key: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    contact_id: int
    order_date: str
    lines: list[LineItemCreate]


class PurchaseBillCreate(BaseModel):
    contact_id: int
    bill_date: str
    purchase_order_id: Optional[int] = None
    lines: list[LineItemCreate] = []


class VendorPaymentCreate(BaseModel):
    purchase_bill_id: int
    amount: Decimal
    payment_date: str
    idempotency_key: Optional[str] = None
