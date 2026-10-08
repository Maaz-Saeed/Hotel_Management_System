from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestUpdate

def get(db: Session, guest_id: int) -> Guest | None:
    return db.get(Guest, guest_id)

def get_by_document(db: Session, id_type: str, id_number: str) -> Guest | None:
    return db.scalar(
        select(Guest).where(Guest.id_type == id_type, Guest.id_number == id_number)
    )

def search(db: Session, q: str | None, skip: int = 0, limit: int = 100) -> list[Guest]:
    stmt = select(Guest).order_by(Guest.full_name)
    if q and q.strip():
        term = q.strip()
        stmt = stmt.where(
            or_(
                Guest.full_name.icontains(term, autoescape=True),
                Guest.phone.icontains(term, autoescape=True),
                Guest.id_number.icontains(term, autoescape=True),
                Guest.email.icontains(term, autoescape=True),
            )
        )
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())

def has_bookings(db: Session, guest_id: int) -> bool:
    return db.scalar(select(Booking.id).where(Booking.guest_id == guest_id).limit(1)) is not None

def create(db: Session, data: GuestCreate) -> Guest:
    values = data.model_dump()
    if values.get("email"):
        values["email"] = values["email"].lower()
    guest = Guest(**values)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest

def update(db: Session, guest: Guest, data: GuestUpdate) -> Guest:
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is None and field not in ("email", "address"):
            continue
        if field == "email" and value:
            value = value.lower()
        setattr(guest, field, value)
    db.commit()
    db.refresh(guest)
    return guest

def delete(db: Session, guest: Guest) -> None: 
    db.delete(guest)
    db.commit()
