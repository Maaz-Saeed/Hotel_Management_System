from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate
from app.services.booking_service import BookingError


def total_paid(db: Session, booking_id: int) -> Decimal:
    stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.booking_id == booking_id, Payment.status == "completed"
    )
    return Decimal(str(db.scalar(stmt)))


def get_balance(db: Session, booking: Booking) -> dict:
    paid = total_paid(db, booking.id)
    due = booking.total_amount - paid
    if paid <= 0:
        payment_status = "unpaid"
    elif due > 0:
        payment_status = "partial"
    else:
        payment_status = "paid"
    return {
        "booking_id": booking.id,
        "total_amount": booking.total_amount,
        "total_paid": paid,
        "balance_due": due,
        "payment_status": payment_status,
    }


def create_payment(db: Session, data: PaymentCreate) -> Payment:
    booking = db.scalar(
        select(Booking).where(Booking.id == data.booking_id).with_for_update()
    )
    if booking is None:
        raise BookingError(404, "Booking not found")
    if booking.status == "cancelled":
        raise BookingError(409, "Cannot take a payment for a cancelled booking")

    due = booking.total_amount - total_paid(db, booking.id)
    if data.amount > due:
        raise BookingError(409, f"Amount is more than the balance due ({due})")

    payment = Payment(
        booking_id=booking.id, amount=data.amount, method=data.method, status="completed"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
