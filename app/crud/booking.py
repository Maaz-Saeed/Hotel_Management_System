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
) -> list[Booking]:
    stmt = _with_relations(select(Booking)).order_by(Booking.id.desc())
    if guest_id:
        stmt = stmt.where(Booking.guest_id == guest_id)
    if room_id: 
        stmt = stmt.where(Booking.room_id == room_id)
    if status: 
        stmt = stmt.where(Booking.status == status)
    return list(db.scalars(stmt.offset(skip).limit(limit)).unique().all())
