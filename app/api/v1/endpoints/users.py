from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.crud import user as crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix= "/users", tags=["Users"])

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_role("admin"))]

EMAIL_TAKEN = "A user with this email already exists"

def get_or_404(db: Session, user_id: int) -> User:
    user = crud.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail= "User not found.")
    return user

@router.get("", response_model= list[UserOut])
def list_users(
    db: DbSession,
    admin: AdminUser,
    skip: Annotated[int, Query(ge= 0)] = 0,
    limit: Annotated[int, Query(ge= 100)] = 100,
):
    return crud.list_all(db, skip, limit)

@router.get("/{user_id}", response_model= UserOut)
def read_user(user_id: int, db: DbSession, admin: AdminUser):
    return get_or_404(db, user_id)

@router.post("", response_model= UserOut, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: DbSession, admin: AdminUser):
    if crud.get_by_email(db, data.email):
        raise HTTPException(status_code=409, detail= EMAIL_TAKEN)
    try:
        return crud.create_user(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail= EMAIL_TAKEN)

@router.patch("/{user_id}", response_model= UserOut)
def updata_user(user_id: int, data: UserUpdate, db: DbSession, admin: AdminUser):
    user = get_or_404(db, user_id)
    if data.email:
        existing = crud.get_by_email(db, data.email)
        if existing and existing.id != user.id:
            raise HTTPException(status_code= 409, detail= EMAIL_TAKEN)
        if user.id == admin.id:
            if data.is_active is False:
                raise HTTPException(status_code= 409, detail= "You cannot deactivate your own account")
            if data.role and data.role != "admin":
                raise HTTPException(status_code= 409, detail= "You cannot remove your own admin role")
        try: 
            return crud.update_user(db, user, data)
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code= 409, detail= EMAIL_TAKEN)
        