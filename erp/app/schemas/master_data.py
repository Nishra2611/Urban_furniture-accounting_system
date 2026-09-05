from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.models.enums import PartyType, AccountType


class ContactCreate(BaseModel):
    code: str
    name: str
    party_type: PartyType
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    image_url: Optional[str] = None
    receivable_account_id: Optional[int] = None
    payable_account_id: Optional[int] = None


class ContactOut(ContactCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    product_type: str = "Goods"
    category: Optional[str] = None
    image_url: Optional[str] = None
    sales_price: Decimal = Decimal("0")
    purchase_price: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    track_stock: bool = False
    income_account_id: Optional[int] = None
    expense_account_id: Optional[int] = None


class ProductOut(ProductCreate):
    id: int
    is_active: bool
    stock_quantity: Decimal

    class Config:
        from_attributes = True


class TaxCreate(BaseModel):
    name: str
    rate: Decimal
    tax_type: str


class TaxOut(TaxCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class ChartOfAccountCreate(BaseModel):
    code: str
    name: str
    account_type: AccountType
    parent_id: Optional[int] = None


class ChartOfAccountOut(ChartOfAccountCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class JournalCreate(BaseModel):
    code: str
    name: str
    journal_type: str = "Miscellaneous"
    default_debit_account_id: Optional[int] = None
    default_credit_account_id: Optional[int] = None


class JournalOut(JournalCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class JournalEntryLineCreate(BaseModel):
    account_id: int
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: Optional[str] = None


class JournalEntryCreate(BaseModel):
    journal_id: int
    entry_date: str
    narration: Optional[str] = None
    analytic_account_id: Optional[int] = None
    lines: list[JournalEntryLineCreate]


class JournalEntryOut(BaseModel):
    id: int
    entry_number: str
    journal_id: int
    entry_date: str
    status: str
    lines: list[JournalEntryLineCreate]

    class Config:
        from_attributes = True


class AnalyticAccountCreate(BaseModel):
    code: str
    name: str
    type: str = "Expense"


class AnalyticAccountOut(AnalyticAccountCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class AnalyticBudgetCreate(BaseModel):
    name: str
    analytic_account_id: int
    period_start: str
    period_end: str
    budget_amount: Decimal
    responsible_name: Optional[str] = None
    stage: str = "Draft"
    revised_with: Optional[str] = None
    revision_of: Optional[str] = None


class AnalyticBudgetOut(AnalyticBudgetCreate):
    id: int

    class Config:
        from_attributes = True
