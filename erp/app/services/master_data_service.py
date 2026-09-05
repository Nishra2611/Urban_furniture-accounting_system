from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.master_data import Contact, Product, Tax, ChartOfAccount, AnalyticAccount, AnalyticBudget
from app.models.user import User, PasswordHistory
from app.models.enums import UserRole
from app.core.security import hash_password, validate_password_strength
from app.schemas.master_data import (
    ContactCreate, ProductCreate, TaxCreate, ChartOfAccountCreate, JournalCreate,
    AnalyticAccountCreate, AnalyticBudgetCreate,
)
from app.models.accounting import Journal


def _unique_or_409(db: Session, model, code: str):
    if db.query(model).filter(model.code == code).first():
        raise HTTPException(status_code=409, detail=f"{model.__name__} code already exists")


def create_contact(db: Session, payload: ContactCreate) -> Contact:
    _unique_or_409(db, Contact, payload.code)
    values = payload.model_dump(exclude={"create_portal_user", "portal_login_id", "portal_password"})
    contact = Contact(**values)
    db.add(contact)
    db.flush()
    if payload.create_portal_user:
        if not payload.email or not payload.portal_login_id or not payload.portal_password:
            raise HTTPException(status_code=422, detail="Portal user requires email, login ID, and password")
        password_error = validate_password_strength(payload.portal_password)
        if password_error:
            raise HTTPException(status_code=422, detail=password_error)
        if db.query(User).filter(User.login_id == payload.portal_login_id).first():
            raise HTTPException(status_code=409, detail="Portal login ID already exists")
        if db.query(User).filter(User.email.ilike(str(payload.email))).first():
            raise HTTPException(status_code=409, detail="Portal email already has a user")
        portal_user = User(name=contact.name, login_id=payload.portal_login_id,
                           email=str(payload.email), hashed_password=hash_password(payload.portal_password),
                           role=UserRole.USER, is_active=True, contact_id=contact.id)
        db.add(portal_user)
        db.flush()
        db.add(PasswordHistory(user_id=portal_user.id, hashed_password=portal_user.hashed_password,
                               created_at=datetime.now(timezone.utc)))
    db.commit()
    db.refresh(contact)
    return contact


def create_product(db: Session, payload: ProductCreate) -> Product:
    _unique_or_409(db, Product, payload.code)
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def create_tax(db: Session, payload: TaxCreate) -> Tax:
    if payload.rate < 0:
        raise HTTPException(status_code=422, detail="Tax rate cannot be negative")
    if payload.tax_type not in ("percentage", "fixed"):
        raise HTTPException(status_code=422, detail="Tax type must be percentage or fixed")
    tax = Tax(**payload.model_dump())
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return tax


def create_account(db: Session, payload: ChartOfAccountCreate) -> ChartOfAccount:
    _unique_or_409(db, ChartOfAccount, payload.code)
    account = ChartOfAccount(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_journal(db: Session, payload: JournalCreate) -> Journal:
    _unique_or_409(db, Journal, payload.code)
    journal = Journal(**payload.model_dump())
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal


def create_analytic_account(db: Session, payload: AnalyticAccountCreate) -> AnalyticAccount:
    _unique_or_409(db, AnalyticAccount, payload.code)
    acc = AnalyticAccount(**payload.model_dump())
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def create_analytic_budget(db: Session, payload: AnalyticBudgetCreate) -> AnalyticBudget:
    if not db.query(AnalyticAccount).filter(AnalyticAccount.id == payload.analytic_account_id).first():
        raise HTTPException(status_code=404, detail="Analytic account not found")
    budget = AnalyticBudget(**payload.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def deactivate(db: Session, model, obj_id: int):
    """Archive instead of hard-delete, so historical transactions keep a valid reference."""
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    obj.is_active = False
    db.commit()
    return obj


def update_record(db: Session, model, obj_id: int, payload) :
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    values = payload.model_dump(exclude_unset=True)
    if model is Contact:
        values = {key: value for key, value in values.items()
                  if key not in {"create_portal_user", "portal_login_id", "portal_password"}}
    if "code" in values and values["code"] != getattr(obj, "code", values["code"]):
        duplicate = db.query(model).filter(model.code == values["code"], model.id != obj_id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail=f"{model.__name__} code already exists")
    for key, value in values.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def get_active_or_404(db: Session, model, obj_id: int, allow_inactive: bool = False):
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    if not allow_inactive and hasattr(obj, "is_active") and not obj.is_active:
        raise HTTPException(status_code=422, detail=f"{model.__name__} is inactive and cannot be used")
    return obj
