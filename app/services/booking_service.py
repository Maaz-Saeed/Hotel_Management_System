from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.room import Room

ACTIVE_STATUSES = ("reserved", "checked_in")


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
