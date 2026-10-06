from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail= "Could not validate credentials",
        headers= {"WWW-Authenticate": "Bearer"},
    )
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception
    user = crud_user.get_by_email(db, email)
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def require_role(*allowed_roles: str):
    def checker(
            current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= "You do not have permission to do this",
            )
        return current_user

    return checker
