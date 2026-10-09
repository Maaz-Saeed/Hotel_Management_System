from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.crud import payment as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services import billing_service
from app.services.booking_service import BookingError

router = APIRouter(prefix="/payments", tags=["Payments"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
StaffUser = Annotated[User, Depends(require_role("admin", "receptionist"))]


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(data: PaymentCreate, db: DbSession, staff: StaffUser):
    try:
        return billing_service.create_payment(db, data)
    except BookingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("", response_model=list[PaymentOut])
def list_payments(
    db: DbSession,
    user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    booking_id: int | None = None,
):
    return crud.list_all(db, skip, limit, booking_id)


@router.get("/{payment_id}", response_model=PaymentOut)
def read_payment(payment_id: int, db: DbSession, user: CurrentUser):
    payment = crud.get(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
