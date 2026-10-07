from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.crud import room_type as crud
from app.db.session import get_db
from app.models.room_type import RoomType
from app.models.user import User
from app.schemas.room_type import RoomTypeCreate, RoomTypeOut, RoomTypeUpdate

router = APIRouter(prefix= "/room-type", tags= ["Room Types"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role("admin"))]

def get_or_404(db: Session, room_type_id: int) -> RoomType:
    room_type = crud.get(db, room_type_id)
    if room_type is None:
        raise HTTPException(status_code=404, detail="Room type not found ")
    return room_type

@router.get("", response_model= list[RoomTypeOut])
def list_room_types(
    db: DbSession,
    user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return crud.list_all(db, skip, limit)

@router.get("/{room_type_id}", response_model=RoomTypeOut)
def read_room_type(room_type_id: int, db: DbSession, user: CurrentUser):
    return get_or_404(db, room_type_id)

@router.post("", response_model=RoomTypeOut, status_code=status.HTTP_201_CREATED)
def create_room_type(data: RoomTypeOut, db: DbSession, admin: AdminUser):
    if crud.get_by_name(db, data.name):
        raise HTTPException(status_code=409, detail= "A room type with this name already exists")
    return crud.create(db, data)

@router.patch("/{room_type_id}", response_model=RoomTypeOut)
def update_room_type(room_type_id: int, data: RoomTypeUpdate, db: DbSession, admin: AdminUser):
    room_type = get_or_404(db, room_type_id)
    if data.name: 
        existing = crud.get_by_name(db, data.name)
        if existing and existing.id != room_type_id:
            raise HTTPException(status_code=409, detail= "A room type with this name already exists")
    return crud.update(db, room_type, data)

@router.delete("/{room_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_type(room_type_id: int, db: DbSession, admin: AdminUser):
    room_type = get_or_404(db, room_type_id)
    if room_type.rooms:
        raise HTTPException(status_code=409, detail= "This room type still has rooms. Move ro delete those rooms first.")
    crud.delete(db, room_type)