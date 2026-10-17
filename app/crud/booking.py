from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.room import Room


def _with_relations(stmt):
    return stmt.options(
        joinedload(Booking.guest),
        joinedload(Booking.room).joinedload(Room.room_type),
    )


def get(db: Session, booking_id: int) -> Booking | None:
    stmt = _with_relations(select(Booking).where(Booking.id == booking_id))
    return db.scalar(stmt)


def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    guest_id: int | None = None,
    room_id: int | None = None,
    status: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> list[Booking]:
    stmt = _with_relations(select(Booking)).order_by(Booking.check_in.desc(), Booking.id.desc())
    if guest_id:
        stmt = stmt.where(Booking.guest_id == guest_id)
    if room_id:
        stmt = stmt.where(Booking.room_id == room_id)
    if status:
        stmt = stmt.where(Booking.status == status)
    if start and end:  # stays that overlap [start, end)
        stmt = stmt.where(Booking.check_in < end, Booking.check_out > start)
    return list(db.scalars(stmt.offset(skip).limit(limit)).unique().all())


def list_arrivals(db: Session, day) -> list[Booking]:
    stmt = (
        _with_relations(select(Booking))
        .where(Booking.status != "cancelled", Booking.check_in == day)
        .order_by(Booking.id)
    )
    return list(db.scalars(stmt).unique().all())


def list_departures(db: Session, day) -> list[Booking]:
    stmt = (
        _with_relations(select(Booking))
        .where(
            Booking.status.in_(("checked_in", "checked_out")),
            Booking.check_out == day,
        )
        .order_by(Booking.id)
    )
    return list(db.scalars(stmt).unique().all())
