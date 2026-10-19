from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.mail import send_email
from app.core.reset import fingerprint, make_reset_token, read_reset_token
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models.customer import Customer
from app.models.user import User
from app.schemas.password import ChangePasswordIn, ForgotIn, ResetIn

router = APIRouter(tags=["Password"])
SAME_ANSWER = {"message": "If that email is registered, a reset link has been sent."}


def _forgot(db: Session, background: BackgroundTasks, model, kind: str, email: str, page: str):
    account = db.scalar(select(model).where(model.email == email.lower()))
    if account is not None and getattr(account, "is_active", True):
        token = make_reset_token(kind, account.email, account.hashed_password)
        link = f"{settings.PUBLIC_BASE_URL.rstrip('/')}{page}?reset={token}"
        body = f"Hello {account.full_name},\n\nUse this link to set a new password (valid for 30 minutes):\n{link}\n\nIf you did not ask for this, ignore this email."
        background.add_task(send_email, account.email, "Reset your Grand Hotel password", body)
    return SAME_ANSWER  # same answer for known and unknown emails


def _reset(db: Session, model, kind: str, data: ResetIn):
    found = read_reset_token(data.token, kind)
    account = db.scalar(select(model).where(model.email == found[0])) if found else None
    if account is None or fingerprint(account.hashed_password) != found[1]:
        raise HTTPException(400, "This reset link is invalid or has expired")
    account.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated. You can sign in now."}


@router.post("/auth/forgot")
def staff_forgot(data: ForgotIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    return _forgot(db, background, User, "staff", data.email, "/app/")


@router.post("/auth/reset")
def staff_reset(data: ResetIn, db: Session = Depends(get_db)):
    return _reset(db, User, "staff", data)


@router.post("/auth/change-password")
def change_password(data: ChangePasswordIn, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")
    if data.current_password == data.new_password:
        raise HTTPException(400, "New password must be different from the current one")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed"}


@router.post("/public/auth/forgot")
def customer_forgot(data: ForgotIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    return _forgot(db, background, Customer, "customer", data.email, "/")


@router.post("/public/auth/reset")
def customer_reset(data: ResetIn, db: Session = Depends(get_db)):
    return _reset(db, Customer, "customer", data)
