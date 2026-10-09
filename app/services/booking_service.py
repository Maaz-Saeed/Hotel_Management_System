from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.guest import Guest
from app.models.room import Room
from app.models.user import User
from app.schemas.booking import BookingCreate

ACTIVE_STATUSES = ("reserved", "checked_in")


class BookingError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def overlapping_booking_exists(
    db: Session, room_id: int, check_in: date, check_out: date
) -> bool:
    stmt = (
        select(Booking.id)
        .where(
            Booking.room_id == room_id,
            Booking.status.in_(ACTIVE_STATUSES),
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


def find_available_rooms(
    db: Session, check_in: date, check_out: date, room_type_id: int | None = None
) -> list[Room]:
    booked_room_ids = select(Booking.room_id).where(
        Booking.status.in_(ACTIVE_STATUSES),
        Booking.check_in < check_out,
        Booking.check_out > check_in,
    )
    stmt = (
        select(Room)
        .options(joinedload(Room.room_type))
        .where(Room.status == "available", Room.id.not_in(booked_room_ids))
        .order_by(Room.room_number)
    )
    if room_type_id:
        stmt = stmt.where(Room.room_type_id == room_type_id)
    return list(db.scalars(stmt).all())


def calculate_total(room: Room, check_in: date, check_out: date) -> Decimal:
    nights = (check_out - check_in).days
    return room.room_type.base_price * nights


def create_booking(db: Session, data: BookingCreate, user: User) -> Booking:
    guest = db.get(Guest, data.guest_id)
    if guest is None:
        raise BookingError(404, "Guest not found")

    room = db.get(Room, data.room_id)
    if room is None:
        raise BookingError(404, "Room not found")
    if room.status != "available":
        raise BookingError(409, "This room is under maintenance and cannot be booked")

    if overlapping_booking_exists(db, room.id, data.check_in, data.check_out):
        raise BookingError(409, "This room is already booked for these dates")

    booking = Booking(
        guest_id=guest.id,
        room_id=room.id,
        created_by=user.id,
        check_in=data.check_in,
        check_out=data.check_out,
        status="reserved",
        total_amount=calculate_total(room, data.check_in, data.check_out),
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BookingError(409, "This room is already booked for these dates")
    db.refresh(booking)
    return booking

def _get_booking_or_404(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise BookingError(404, "Booking not found")
    return booking


def check_in(db: Session, booking_id: int) -> Booking:
    booking = _get_booking_or_404(db, booking_id)
    if booking.status != "reserved":
        raise BookingError(
            409, f"Only reserved bookings can be checked in (current status: {booking.status})"
        )
    if date.today() < booking.check_in:
        raise BookingError(409, "Check-in is not allowed before the check-in date")
    booking.status = "checked_in"
    db.commit()
    db.refresh(booking)
    return booking


def check_out(db: Session, booking_id: int) -> Booking:
    booking = _get_booking_or_404(db, booking_id)
    if booking.status != "checked_in":
        raise BookingError(
            409, f"Only checked-in bookings can be checked out (current status: {booking.status})"
        )
    booking.status = "checked_out"
    db.commit()
    db.refresh(booking)
    return booking


def cancel_booking(db: Session, booking_id: int) -> Booking:
    booking = _get_booking_or_404(db, booking_id)
    if booking.status != "reserved":
        raise BookingError(
            409, f"Only reserved bookings can be cancelled (current status: {booking.status})"
        )
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking
