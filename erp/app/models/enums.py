import enum


class UserRole(str, enum.Enum):
    USER = "User"
    ACCOUNTANT = "Accountant"
    ADMINISTRATOR = "Administrator"


class DocumentStatus(str, enum.Enum):
    DRAFT = "Draft"
    CONFIRMED = "Confirmed"
    POSTED = "Posted"
    CANCELLED = "Cancelled"


class PaymentStatus(str, enum.Enum):
    UNPAID = "Unpaid"
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"


class PartyType(str, enum.Enum):
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    BOTH = "Both"


class AccountType(str, enum.Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"


class PaymentTargetType(str, enum.Enum):
    SALE_INVOICE = "SaleInvoice"
    PURCHASE_BILL = "PurchaseBill"


class PaymentDirection(str, enum.Enum):
    RECEIPT = "Receipt"   # money in, against a Sale Invoice
    PAYMENT = "Payment"   # money out, against a Purchase Bill
