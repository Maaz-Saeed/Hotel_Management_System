from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session 

from app.api.deps import get_current_user, require_role
from app.crud import guest as crud
from app.db.session import get_db
from app.models.guest import Guest
from app.models.user import User
from app.schemas.guest import GuestCreate, GuestUpdate, GuestOut

router = APIRouter (prefix="/guests", tags=["Guests"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
StaffUser = Annotated[User, Depends(require_role("admin", "receptionist"))]
AdminUser = Annotated[User, Depends(require_role("admin"))]

DUPLICATE_MSG = "At guest with this ID type and ID number already exists"

def get_or_404(db: Session, guest_id: int) -> Guest:
    guest = crud.get(db, guest_id)
    if guest is None:
        raise HTTPException(status_code=404, detail="Guest not found.")
    return guest

@router.get("", response_model=list[GuestOut])
def search_guests(
    db: DbSession,
    user: CurrentUser,
    q: Annotated[str | None, Query(max_length=100)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    return crud.search(db, q, skip, limit)

@router.get("/{guest_id}", response_model=GuestOut)
def read_guest(guest_id: int, db: DbSession, user: CurrentUser):
    return get_or_404(db, guest_id)

@router.post("", response_model= GuestOut, status_code=status.HTTP_201_CREATED)
def create_guest(data: GuestCreate, db: DbSession, staff: StaffUser):
    if crud.get_by_document(db, data.id_type, data.id_number):
        raise HTTPException(status_code=409, detail=DUPLICATE_MSG)
    try:
        return crud.create(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=DUPLICATE_MSG)

@router.patch("/{guest_id}", response_model=GuestOut)
def update_guest(guest_id: int, data: GuestUpdate, db: DbSession, staff: StaffUser):
    guest = get_or_404(db, guest_id)
    new_type = data.id_type or guest.id_type
    new_number = data.id_number or guest.id_number
    existing = crud.get_by_document(db, new_type, new_number)
    if existing and existing.id != guest.id: 
        raise HTTPException(status_code=409, detail=DUPLICATE_MSG)
    try:
        return crud.update(db, guest, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=DUPLICATE_MSG)

@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(guest_id: int, db: DbSession, admin: AdminUser):
    guest = get_or_404(db, guest_id)
    if crud.has_bookings(db, guest.id):
        raise HTTPException(
            status_code= 409,
            detail= "This guest has booking and annot be deleted",
        )
    crud.delete(db, guest)
