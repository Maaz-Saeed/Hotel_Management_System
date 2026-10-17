from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.crud import booking as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut, BookingStatus
from app.schemas.payment import BalanceOut
from app.services import billing_service, booking_service
from app.services.booking_service import BookingError

router = APIRouter(prefix="/bookings", tags=["Bookings"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
StaffUser = Annotated[User, Depends(require_role("admin", "receptionist"))]


def date_window(year: int | None, month: int | None, day: int | None):
    """Turn year / month / day into a [start, end) window. Day needs month, month needs year."""
    if (day and not month) or (month and not year):
        raise HTTPException(status_code=422, detail="Day needs a month, and month needs a year")
    if not year:
        return None, None
    try:
        if day:
            start = date(year, month, day)
            return start, start + timedelta(days=1)
        if month:
            return date(year, month, 1), date(year + (month == 12), month % 12 + 1, 1)
        return date(year, 1, 1), date(year + 1, 1, 1)
    except ValueError:
        raise HTTPException(status_code=422, detail="That date does not exist")


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(data: BookingCreate, db: DbSession, staff: StaffUser):
    try:
        return booking_service.create_booking(db, data, staff)
    except BookingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("", response_model=list[BookingOut])
def list_bookings(
    db: DbSession,
    user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    guest_id: int | None = None,
    room_id: int | None = None,
    booking_status: Annotated[BookingStatus | None, Query(alias="status")] = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    day: Annotated[int | None, Query(ge=1, le=31)] = None,
):
    start, end = date_window(year, month, day)
    return crud.list_all(db, skip, limit, guest_id, room_id, booking_status, start, end)


@router.get("/{booking_id}", response_model=BookingOut)
def read_booking(booking_id: int, db: DbSession, user: CurrentUser):
    booking = crud.get(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


def _run(action, db: Session, booking_id: int):
    try:
        return action(db, booking_id)
    except BookingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{booking_id}/check-in", response_model=BookingOut)
def check_in_booking(booking_id: int, db: DbSession, staff: StaffUser):
    return _run(booking_service.check_in, db, booking_id)


@router.post("/{booking_id}/check-out", response_model=BookingOut)
def check_out_booking(booking_id: int, db: DbSession, staff: StaffUser):
    return _run(booking_service.check_out, db, booking_id)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: int, db: DbSession, staff: StaffUser):
    return _run(booking_service.cancel_booking, db, booking_id)


@router.get("/{booking_id}/balance", response_model=BalanceOut)
def booking_balance(booking_id: int, db: DbSession, user: CurrentUser):
    booking = crud.get(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return billing_service.get_balance(db, booking)
