from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin, require_admin
from app.models.user import User
from app.models.master_data import Contact, Product, Tax, ChartOfAccount, AnalyticAccount, AnalyticBudget
from app.models.accounting import Journal
from app.schemas.master_data import (
    ContactCreate, ContactOut, ProductCreate, ProductOut, TaxCreate, TaxOut,
    ChartOfAccountCreate, ChartOfAccountOut, JournalCreate, JournalOut,
    AnalyticAccountCreate, AnalyticAccountOut, AnalyticBudgetCreate, AnalyticBudgetOut,
    BulkIDsReq,
)
from app.services import master_data_service as svc

router = APIRouter(prefix="/api/v1", tags=["master-data"])


# --- Contacts ---
@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_contact(db, payload)


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(include_archived: bool = False, db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    query = db.query(Contact)
    if not include_archived:
        query = query.filter(Contact.is_active.is_(True))
    return query.all()


@router.post("/contacts/{contact_id}/deactivate", response_model=ContactOut)
def deactivate_contact(contact_id: int, db: Session = Depends(get_db),
                        _: User = Depends(require_admin)):
    return svc.deactivate(db, Contact, contact_id)


@router.post("/contacts/{contact_id}/activate", response_model=ContactOut)
def activate_contact(contact_id: int, db: Session = Depends(get_db),
                     _: User = Depends(require_admin)):
    return svc.activate_record(db, Contact, contact_id)


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    return svc.delete_record(db, Contact, contact_id)


@router.put("/contacts/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: int, payload: ContactCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_accountant_or_admin)):
    return svc.update_record(db, Contact, contact_id, payload)


@router.post("/contacts/bulk-archive")
def bulk_archive_contacts(payload: BulkIDsReq, db: Session = Depends(get_db),
                          _: User = Depends(require_admin)):
    return svc.bulk_archive(db, Contact, payload.ids)


@router.post("/contacts/bulk-delete")
def bulk_delete_contacts(payload: BulkIDsReq, db: Session = Depends(get_db),
                         _: User = Depends(require_admin)):
    return svc.bulk_delete(db, Contact, payload.ids)


# --- Products ---
@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_product(db, payload)


@router.get("/products", response_model=list[ProductOut])
def list_products(include_archived: bool = False, db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    query = db.query(Product)
    if not include_archived:
        query = query.filter(Product.is_active.is_(True))
    return query.all()


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_accountant_or_admin)):
    return svc.update_record(db, Product, product_id, payload)


@router.post("/products/{product_id}/deactivate", response_model=ProductOut)
def deactivate_product(product_id: int, db: Session = Depends(get_db),
                        _: User = Depends(require_admin)):
    return svc.deactivate(db, Product, product_id)


@router.post("/products/{product_id}/activate", response_model=ProductOut)
def activate_product(product_id: int, db: Session = Depends(get_db),
                     _: User = Depends(require_admin)):
    return svc.activate_record(db, Product, product_id)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    return svc.delete_record(db, Product, product_id)


@router.post("/products/bulk-archive")
def bulk_archive_products(payload: BulkIDsReq, db: Session = Depends(get_db),
                           _: User = Depends(require_admin)):
    return svc.bulk_archive(db, Product, payload.ids)


@router.post("/products/bulk-delete")
def bulk_delete_products(payload: BulkIDsReq, db: Session = Depends(get_db),
                          _: User = Depends(require_admin)):
    return svc.bulk_delete(db, Product, payload.ids)


# --- Taxes ---
@router.post("/taxes", response_model=TaxOut, status_code=201)
def create_tax(payload: TaxCreate, db: Session = Depends(get_db),
               _: User = Depends(require_accountant_or_admin)):
    return svc.create_tax(db, payload)


@router.get("/taxes", response_model=list[TaxOut])
def list_taxes(include_archived: bool = False, db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    query = db.query(Tax)
    if not include_archived:
        query = query.filter(Tax.is_active.is_(True))
    return query.all()


@router.put("/taxes/{tax_id}", response_model=TaxOut)
def update_tax(tax_id: int, payload: TaxCreate, db: Session = Depends(get_db),
               _: User = Depends(require_accountant_or_admin)):
    return svc.update_record(db, Tax, tax_id, payload)


@router.post("/taxes/{tax_id}/deactivate", response_model=TaxOut)
def deactivate_tax(tax_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    return svc.deactivate(db, Tax, tax_id)


@router.post("/taxes/{tax_id}/activate", response_model=TaxOut)
def activate_tax(tax_id: int, db: Session = Depends(get_db),
                 _: User = Depends(require_admin)):
    return svc.activate_record(db, Tax, tax_id)


@router.delete("/taxes/{tax_id}")
def delete_tax(tax_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_admin)):
    return svc.delete_record(db, Tax, tax_id)


@router.post("/taxes/bulk-archive")
def bulk_archive_taxes(payload: BulkIDsReq, db: Session = Depends(get_db),
                        _: User = Depends(require_admin)):
    return svc.bulk_archive(db, Tax, payload.ids)


@router.post("/taxes/bulk-delete")
def bulk_delete_taxes(payload: BulkIDsReq, db: Session = Depends(get_db),
                       _: User = Depends(require_admin)):
    return svc.bulk_delete(db, Tax, payload.ids)


# --- Chart of Accounts (COA Protected) ---
SYSTEM_COA_CODES = {"1000", "1200", "2000", "3000", "4000", "5000"}

@router.post("/chart-of-accounts", response_model=ChartOfAccountOut, status_code=201)
def create_account(payload: ChartOfAccountCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_account(db, payload)


@router.get("/chart-of-accounts", response_model=list[ChartOfAccountOut])
def list_accounts(include_archived: bool = False, db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    query = db.query(ChartOfAccount)
    if not include_archived:
        query = query.filter(ChartOfAccount.is_active.is_(True))
    return query.all()


@router.put("/chart-of-accounts/{account_id}", response_model=ChartOfAccountOut)
def update_account(account_id: int, payload: ChartOfAccountCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_accountant_or_admin)):
    acc = db.query(ChartOfAccount).filter(ChartOfAccount.id == account_id).first()
    if acc and acc.code in SYSTEM_COA_CODES:
        if payload.code != acc.code:
            raise HTTPException(status_code=422, detail="System default COA account codes cannot be modified.")
    return svc.update_record(db, ChartOfAccount, account_id, payload)


@router.post("/chart-of-accounts/{account_id}/deactivate", response_model=ChartOfAccountOut)
def deactivate_account(account_id: int, db: Session = Depends(get_db),
                       _: User = Depends(require_admin)):
    acc = db.query(ChartOfAccount).filter(ChartOfAccount.id == account_id).first()
    if acc and acc.code in SYSTEM_COA_CODES:
        raise HTTPException(status_code=422, detail="System default COA accounts cannot be archived.")
    return svc.deactivate(db, ChartOfAccount, account_id)


# --- Journals ---
@router.post("/journals", response_model=JournalOut, status_code=201)
def create_journal(payload: JournalCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_journal(db, payload)


@router.get("/journals", response_model=list[JournalOut])
def list_journals(include_archived: bool = False, db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    query = db.query(Journal)
    if not include_archived:
        query = query.filter(Journal.is_active.is_(True))
    return query.all()


@router.put("/journals/{journal_id}", response_model=JournalOut)
def update_journal(journal_id: int, payload: JournalCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_accountant_or_admin)):
    return svc.update_record(db, Journal, journal_id, payload)


@router.post("/journals/{journal_id}/deactivate", response_model=JournalOut)
def deactivate_journal(journal_id: int, db: Session = Depends(get_db),
                       _: User = Depends(require_admin)):
    return svc.deactivate(db, Journal, journal_id)


# --- Analytic Accounts ---
@router.post("/analytic-accounts", response_model=AnalyticAccountOut, status_code=201)
def create_analytic_account(payload: AnalyticAccountCreate, db: Session = Depends(get_db),
                             _: User = Depends(require_accountant_or_admin)):
    return svc.create_analytic_account(db, payload)


@router.get("/analytic-accounts", response_model=list[AnalyticAccountOut])
def list_analytic_accounts(include_archived: bool = False, db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    query = db.query(AnalyticAccount)
    if not include_archived:
        query = query.filter(AnalyticAccount.is_active.is_(True))
    return query.all()


@router.put("/analytic-accounts/{account_id}", response_model=AnalyticAccountOut)
def update_analytic_account(account_id: int, payload: AnalyticAccountCreate, db: Session = Depends(get_db),
                            _: User = Depends(require_accountant_or_admin)):
    return svc.update_record(db, AnalyticAccount, account_id, payload)


@router.post("/analytic-accounts/{account_id}/deactivate", response_model=AnalyticAccountOut)
def deactivate_analytic_account(account_id: int, db: Session = Depends(get_db),
                                _: User = Depends(require_admin)):
    return svc.deactivate(db, AnalyticAccount, account_id)


@router.post("/analytic-accounts/{account_id}/activate", response_model=AnalyticAccountOut)
def activate_analytic_account(account_id: int, db: Session = Depends(get_db),
                               _: User = Depends(require_admin)):
    return svc.activate_record(db, AnalyticAccount, account_id)


@router.delete("/analytic-accounts/{account_id}")
def delete_analytic_account(account_id: int, db: Session = Depends(get_db),
                             _: User = Depends(require_admin)):
    return svc.delete_record(db, AnalyticAccount, account_id)


@router.post("/analytic-accounts/bulk-archive")
def bulk_archive_analytic_accounts(payload: BulkIDsReq, db: Session = Depends(get_db),
                                    _: User = Depends(require_admin)):
    return svc.bulk_archive(db, AnalyticAccount, payload.ids)


@router.post("/analytic-accounts/bulk-delete")
def bulk_delete_analytic_accounts(payload: BulkIDsReq, db: Session = Depends(get_db),
                                   _: User = Depends(require_admin)):
    return svc.bulk_delete(db, AnalyticAccount, payload.ids)


# --- Analytic Budgets ---
@router.post("/analytic-budgets", response_model=AnalyticBudgetOut, status_code=201)
def create_analytic_budget(payload: AnalyticBudgetCreate, db: Session = Depends(get_db),
                            _: User = Depends(require_accountant_or_admin)):
    return svc.create_analytic_budget(db, payload)


@router.get("/analytic-budgets", response_model=list[AnalyticBudgetOut])
def list_analytic_budgets(include_archived: bool = False, db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    query = db.query(AnalyticBudget)
    if not include_archived:
        query = query.filter(AnalyticBudget.stage != "Cancelled")
    return query.all()


@router.put("/analytic-budgets/{budget_id}", response_model=AnalyticBudgetOut)
def update_analytic_budget(budget_id: int, payload: AnalyticBudgetCreate, db: Session = Depends(get_db),
                           _: User = Depends(require_accountant_or_admin)):
    return svc.update_record(db, AnalyticBudget, budget_id, payload)


@router.post("/analytic-budgets/{budget_id}/deactivate", response_model=AnalyticBudgetOut)
def deactivate_analytic_budget(budget_id: int, db: Session = Depends(get_db),
                               _: User = Depends(require_admin)):
    return svc.deactivate(db, AnalyticBudget, budget_id)


@router.post("/analytic-budgets/{budget_id}/activate", response_model=AnalyticBudgetOut)
def activate_analytic_budget(budget_id: int, db: Session = Depends(get_db),
                              _: User = Depends(require_admin)):
    return svc.activate_record(db, AnalyticBudget, budget_id)


@router.delete("/analytic-budgets/{budget_id}")
def delete_analytic_budget(budget_id: int, db: Session = Depends(get_db),
                            _: User = Depends(require_admin)):
    return svc.delete_record(db, AnalyticBudget, budget_id)


@router.post("/analytic-budgets/bulk-archive")
def bulk_archive_analytic_budgets(payload: BulkIDsReq, db: Session = Depends(get_db),
                                   _: User = Depends(require_admin)):
    return svc.bulk_archive(db, AnalyticBudget, payload.ids)


@router.post("/analytic-budgets/bulk-delete")
def bulk_delete_analytic_budgets(payload: BulkIDsReq, db: Session = Depends(get_db),
                                  _: User = Depends(require_admin)):
    return svc.bulk_delete(db, AnalyticBudget, payload.ids)
