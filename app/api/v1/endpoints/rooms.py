from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.crud import room as crud
from app.crud import room_type as crud_room_type
from app.db.session import get_db
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate, RoomOut, RoomStatus, RoomUpdate

router = APIRouter(prefix="/rooms", tags=["Rooms"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role("admin"))]

def get_or_404(db: Session, room_id: int) -> Room:
    room = crud.get(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.get("", response_model=list[RoomOut])
def list_rooms(
    db: DbSession,
    user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    room_status: Annotated[RoomStatus | None, Query(alias="status")] = None,
    room_type_id: int | None = None,
    floor: int | None = None,
):
    return crud.list_all(db, skip, limit, room_status, room_type_id, floor)

@router.get("/{room_id}", response_model=RoomOut)
def read_room(room_id: int, db: DbSession, user: CurrentUser):
    return get_or_404(db, room_id)

@router.post("", response_model=RoomOut, status_code= status.HTTP_201_CREATED)
def create_room(data: RoomCreate, db: DbSession, admin: AdminUser):
    if crud.get_by_number(db, data.room_number):
        raise HTTPException(status_code=409, detail="A room with this number already exists")
    if crud_room_type.get(db, data.room_type_id) is None:
        raise HTTPException(status_code=404, detail="Room type not found")
    try:
        return crud.create(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A room with this number already exists")

@router.patch("/{room_id}", response_model=RoomOut)
def update_room(room_id: int, data: RoomUpdate, db: DbSession, admin: AdminUser):
    room = get_or_404(db, room_id)
    if data.room_number:
        existing = crud.get_by_number(db, data.room_number)
        if existing and existing.id != room.id:
            raise HTTPException(status_code=409, detail="A room with this number already exists")
    if data.room_type_id and crud_room_type.get(db, data.room_type_id) is None:
        raise HTTPException(status_code=404, detail="toom type not found")
    return crud.update(db, room, data)

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: DbSession, admin: AdminUser):
    room = get_or_404(db, room_id)
    if crud.has_bookings(db, room.id):
        raise HTTPException(
            status_code=409,
            detail="This room has bookings. Set its status to maintenance instead of deleting it.",
        )
    crud.delete(db, room)
