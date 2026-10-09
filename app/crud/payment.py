from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment


def get(db: Session, payment_id: int) -> Payment | None:
    return db.get(Payment, payment_id)


def list_all(
    db: Session, skip: int = 0, limit: int = 50, booking_id: int | None = None
) -> list[Payment]:
    stmt = select(Payment).order_by(Payment.id.desc())
    if booking_id:
        stmt = stmt.where(Payment.booking_id == booking_id)
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())
