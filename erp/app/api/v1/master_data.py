from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.models.master_data import Contact, Product, Tax, ChartOfAccount, AnalyticAccount, AnalyticBudget
from app.models.accounting import Journal
from app.schemas.master_data import (
    ContactCreate, ContactOut, ProductCreate, ProductOut, TaxCreate, TaxOut,
    ChartOfAccountCreate, ChartOfAccountOut, JournalCreate, JournalOut,
    AnalyticAccountCreate, AnalyticAccountOut, AnalyticBudgetCreate, AnalyticBudgetOut,
)
from app.services import master_data_service as svc

router = APIRouter(prefix="/api/v1", tags=["master-data"])


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_contact(db, payload)


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return db.query(Contact).filter(Contact.is_active.is_(True)).all()


@router.post("/contacts/{contact_id}/deactivate", response_model=ContactOut)
def deactivate_contact(contact_id: int, db: Session = Depends(get_db),
                        _: User = Depends(require_accountant_or_admin)):
    return svc.deactivate(db, Contact, contact_id)


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_product(db, payload)


@router.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return db.query(Product).filter(Product.is_active.is_(True)).all()


@router.post("/taxes", response_model=TaxOut, status_code=201)
def create_tax(payload: TaxCreate, db: Session = Depends(get_db),
               _: User = Depends(require_accountant_or_admin)):
    return svc.create_tax(db, payload)


@router.get("/taxes", response_model=list[TaxOut])
def list_taxes(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return db.query(Tax).filter(Tax.is_active.is_(True)).all()


@router.post("/taxes/{tax_id}/deactivate", response_model=TaxOut)
def deactivate_tax(tax_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_accountant_or_admin)):
    return svc.deactivate(db, Tax, tax_id)


@router.post("/products/{product_id}/deactivate", response_model=ProductOut)
def deactivate_product(product_id: int, db: Session = Depends(get_db),
                        _: User = Depends(require_accountant_or_admin)):
    return svc.deactivate(db, Product, product_id)


@router.post("/chart-of-accounts", response_model=ChartOfAccountOut, status_code=201)
def create_account(payload: ChartOfAccountCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_account(db, payload)


@router.get("/chart-of-accounts", response_model=list[ChartOfAccountOut])
def list_accounts(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return db.query(ChartOfAccount).filter(ChartOfAccount.is_active.is_(True)).all()


@router.post("/journals", response_model=JournalOut, status_code=201)
def create_journal(payload: JournalCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_accountant_or_admin)):
    return svc.create_journal(db, payload)


@router.get("/journals", response_model=list[JournalOut])
def list_journals(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return db.query(Journal).filter(Journal.is_active.is_(True)).all()


@router.post("/analytic-accounts", response_model=AnalyticAccountOut, status_code=201)
def create_analytic_account(payload: AnalyticAccountCreate, db: Session = Depends(get_db),
                             _: User = Depends(require_accountant_or_admin)):
    return svc.create_analytic_account(db, payload)


@router.get("/analytic-accounts", response_model=list[AnalyticAccountOut])
def list_analytic_accounts(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return db.query(AnalyticAccount).filter(AnalyticAccount.is_active.is_(True)).all()


@router.post("/analytic-budgets", response_model=AnalyticBudgetOut, status_code=201)
def create_analytic_budget(payload: AnalyticBudgetCreate, db: Session = Depends(get_db),
                            _: User = Depends(require_accountant_or_admin)):
    return svc.create_analytic_budget(db, payload)


@router.get("/analytic-budgets", response_model=list[AnalyticBudgetOut])
def list_analytic_budgets(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return db.query(AnalyticBudget).all()
