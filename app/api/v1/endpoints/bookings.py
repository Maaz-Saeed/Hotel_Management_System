from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.crud import booking as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut, BookingStatus
from app.services import booking_service
from app.services.booking_service import BookingError

router = APIRouter(prefix="/bookings", tags=["Bookings"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
StaffUser = Annotated[User, Depends(require_role("admin", "receptionist"))]


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
):
    return crud.list_all(db, skip, limit, guest_id, room_id, booking_status)


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