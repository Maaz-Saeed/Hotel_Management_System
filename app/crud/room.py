from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate

def get(db: Session, room_id: int) -> Room | None:
    return db.get(Room, room_id)

def get_by_number(db: Session, room_number: str) -> Room | None:
    return db.scalar(select(Room).where(Room.room_number == room_number))

def list_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        room_type_id: int | None = None,
        floor: int | None = None,
) -> list[Room]:
    stmt = select(Room).options(joinedload(Room.room_type)).order_by(Room.room_number)
    if status: 
        stmt = stmt.where(Room.status == status)
    if room_type_id:
        stmt = stmt.where(Room.room_type_id == room_type_id)
    if floor is not None:
        stmt = stmt.where(Room.floor == floor)
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())

def has_bookings(db: Session, room_id: int) -> bool:
    return db.scalar(select(Booking.id).where(Booking.room_id == room_id).limit(1)) is not None

def create(db: Session, data: RoomCreate) -> Room:
    room = Room(**data.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

def update(db: Session, room: Room, data: RoomUpdate) -> Room:
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None: 
            setattr(room, field, value)
    db.commit()
    db.refresh(room)
    return room

def delete(db: Session, room: Room) -> None: 
    db.delete(room)
    db.commit()
