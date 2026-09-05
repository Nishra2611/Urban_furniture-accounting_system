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


class AnalyticBudgetOut(AnalyticBudgetCreate):
    id: int

    class Config:
        from_attributes = True
