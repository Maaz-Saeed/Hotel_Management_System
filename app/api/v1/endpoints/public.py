import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.booking import Booking
from app.models.guest import Guest
from app.models.room_type import RoomType
from app.schemas.public import OnlineBookingIn, OnlineBookingOut, PublicRoomType
from app.services.booking_service import find_available_rooms

router = APIRouter(prefix="/public", tags=["Public (guests)"])


def to_out(b: Booking) -> OnlineBookingOut:
    return OnlineBookingOut(
        reference=b.reference, status=b.status, room_type=b.room.room_type.name,
        room_number=b.room.room_number, check_in=b.check_in,
        check_out=b.check_out, total_amount=b.total_amount,
    )


def find_booking(db: Session, reference: str, email: str) -> Booking:
    b = db.scalar(
        select(Booking).join(Guest, Booking.guest_id == Guest.id)
        .where(Booking.reference == reference.upper(), func.lower(Guest.email) == email.lower())
    )
    if not b:
        raise HTTPException(404, "No booking found for that reference and email")
    return b


@router.get("/room-types", response_model=list[PublicRoomType])
def list_room_types(check_in: date | None = None, check_out: date | None = None,
                    db: Session = Depends(get_db)):
    if bool(check_in) != bool(check_out):
        raise HTTPException(422, "Send both check_in and check_out")
    if check_in and (check_in < date.today() or check_out <= check_in):
        raise HTTPException(422, "Invalid dates")
    out = []
    for rt in db.scalars(select(RoomType).order_by(RoomType.base_price)):
        item = PublicRoomType.model_validate(rt)
        if check_in:
            item.available_rooms = len(find_available_rooms(db, check_in, check_out, rt.id))
            item.nights = (check_out - check_in).days
            item.total = float(rt.base_price) * item.nights
        out.append(item)
    return out


@router.post("/bookings", response_model=OnlineBookingOut, status_code=201)
def create_online_booking(data: OnlineBookingIn, db: Session = Depends(get_db)):
    rt = db.get(RoomType, data.room_type_id)
    if not rt:
        raise HTTPException(404, "Room type not found")
    nights = (data.check_out - data.check_in).days
    guest = db.scalar(select(Guest).where(func.lower(Guest.email) == data.email.lower()))
    if not guest:
        guest = Guest(full_name=data.full_name, email=data.email.lower(), phone=data.phone)
        db.add(guest)
        db.flush()
    for room in find_available_rooms(db, data.check_in, data.check_out, rt.id):
        booking = Booking(
            guest_id=guest.id, room_id=room.id, created_by=None, source="online",
            check_in=data.check_in, check_out=data.check_out, status="reserved",
            total_amount=rt.base_price * nights, reference="HMS-" + secrets.token_hex(3).upper(),
        )
        try:
            with db.begin_nested():
                db.add(booking)
        except IntegrityError:
            continue  # another request took this room; try the next one
        db.commit()
        db.refresh(booking)
        return to_out(booking)
    db.rollback()
    raise HTTPException(409, "No rooms of this type are free for those dates")


@router.get("/bookings/{reference}", response_model=OnlineBookingOut)
def lookup_booking(reference: str, email: str, db: Session = Depends(get_db)):
    return to_out(find_booking(db, reference, email))


@router.post("/bookings/{reference}/cancel", response_model=OnlineBookingOut)
def cancel_booking(reference: str, email: str, db: Session = Depends(get_db)):
    b = find_booking(db, reference, email)
    if b.status != "reserved":
        raise HTTPException(409, "Only reservations that have not checked in can be cancelled")
    b.status = "cancelled"
    db.commit()
    return to_out(b)
