import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.booking import Booking
from app.models.guest import Guest
from app.models.room import Room
from app.models.room_type import RoomType
from app.schemas.public import OnlineBookingIn, OnlineBookingOut, PublicRoomType
from app.services.booking_service import find_available_rooms

router = APIRouter(prefix="/public", tags=["Public (guests)"])


def free_rooms(db: Session, room_type_id: int, ci: date, co: date):
    rooms = db.scalars(
        select(Room).where(Room.room_type_id == room_type_id, Room.status == "available")
        .order_by(Room.room_number)
    ).all()
    return [r for r in rooms if find_available_rooms(db, r.id, ci, co)]


def to_out(db: Session, b: Booking) -> OnlineBookingOut:
    rt = db.get(RoomType, b.room.room_type_id)
    return OnlineBookingOut(
        reference=b.reference, status=b.status, room_type=rt.name,
        room_number=b.room.room_number, check_in=b.check_in,
        check_out=b.check_out, total_amount=float(b.total_amount),
    )


def find_booking(db: Session, reference: str, email: str) -> Booking:
    b = db.scalar(
        select(Booking).join(Guest, Booking.guest_id == Guest.id)
        .where(Booking.reference == reference.upper(),
               func.lower(Guest.email) == email.lower())
    )
    if not b:
        raise HTTPException(404, "No booking found for that reference and email")
    return b


@router.get("/room-types", response_model=list[PublicRoomType])
def list_room_types(check_in: date | None = None, check_out: date | None = None,
                    db: Session = Depends(get_db)):
    if check_in and check_out and check_out <= check_in:
        raise HTTPException(422, "Check-out must be after check-in")
    out = []
    for rt in db.scalars(select(RoomType).order_by(RoomType.base_price)):
        item = PublicRoomType.model_validate(rt)
        if check_in and check_out:
            item.available_rooms = len(free_rooms(db, rt.id, check_in, check_out))
            item.nights = (check_out - check_in).days
            item.total = float(rt.base_price) * item.nights
        out.append(item)
    return out


@router.post("/bookings", response_model=OnlineBookingOut, status_code=201)
def create_online_booking(data: OnlineBookingIn, db: Session = Depends(get_db)):
    rt = db.get(RoomType, data.room_type_id)
    if not rt:
        raise HTTPException(404, "Room type not found")
    candidates = free_rooms(db, rt.id, data.check_in, data.check_out)
    if not candidates:
        raise HTTPException(409, "No rooms of this type are free for those dates")

    guest = db.scalar(select(Guest).where(func.lower(Guest.email) == data.email.lower()))
    if not guest:
        guest = Guest(full_name=data.full_name, email=data.email, phone=data.phone)
        db.add(guest)
        db.flush()

    nights = (data.check_out - data.check_in).days
    for room in candidates:  # next room if another request just took this one
        booking = Booking(
            guest_id=guest.id, room_id=room.id, check_in=data.check_in,
            check_out=data.check_out, status="reserved", source="online",
            total_amount=rt.base_price * nights,
            reference="HMS-" + secrets.token_hex(3).upper(),
        )
        try:
            with db.begin_nested():
                db.add(booking)
                db.flush()
            db.commit()
            db.refresh(booking)
            return to_out(db, booking)
        except IntegrityError:
            continue
    db.rollback()
    raise HTTPException(409, "Those dates were just taken. Please search again.")


@router.get("/bookings/{reference}", response_model=OnlineBookingOut)
def lookup_booking(reference: str, email: str, db: Session = Depends(get_db)):
    return to_out(db, find_booking(db, reference, email))


@router.post("/bookings/{reference}/cancel", response_model=OnlineBookingOut)
def cancel_booking(reference: str, email: str, db: Session = Depends(get_db)):
    b = find_booking(db, reference, email)
    if b.status != "reserved":
        raise HTTPException(409, "Only reservations that have not checked in can be cancelled")
    b.status = "cancelled"
    db.commit()
    return to_out(db, b)
