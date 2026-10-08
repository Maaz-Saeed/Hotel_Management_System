from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))

def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        full_name = data.full_name,
        email = data.email.lower(),
        hashed_password = hash_password(data.password),
        role = data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)

def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    stmt = select(User).order_by(User.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

def update_user(db: Session, user: User, data: UserUpdate) -> User:
    values = data.model_dump(exclude_unset=True)
    password = values.pop("password", None)
    for field, value in values.items():
        if value is None:
            continue
        if field == "email":
            value = value.lower()
        setattr(user, field, value)
    if password:
        user.hashed_password = hash_password(password)
    db.commit()
    db.refresh(user)
    return user
