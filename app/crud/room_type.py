from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.room_type import RoomType
from app.schemas.room_type import RoomTypeCreate, RoomTypeUpdate

def get(db: Session, room_type_id: int) -> RoomType | None:
    return db.get(RoomType, room_type_id)

def get_by_name(db: Session, name: str) -> RoomType | None:
    return db.scalar(select(RoomType).where(func.lower(RoomType.name) == name.lower()))

def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[RoomType]:
    stmt = select(RoomType).order_by(RoomType.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

def create(db: Session, data: RoomTypeCreate) -> RoomType:
    room_type = RoomType(**data.model_dump())
    db.add(room_type)
    db.commit()
    db.refresh(room_type)
    return room_type

def update(db: Session, room_type: RoomType, data: RoomTypeUpdate) -> RoomType:
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is None and field != "description":
            continue
        setattr(room_type, field, value)
    db.commit()
    db.refresh(room_type)
    return room_type

def delete(db: Session, room_type: RoomType) -> None:
    db.delete(room_type)
    db.commit()
    