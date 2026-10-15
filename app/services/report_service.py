from datetime import date
from decimal import Decimal

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.payment import Payment
from app.models.room import Room
from app.services.booking_service import ACTIVE_STATUSES

REPORT_TZ = "Asia/Karachi"

def occupancy_for_day(db: Session, day: date) -> dict:
    total_rooms = db.scalar(select(func.count(Room.id))) or 0
    maintenance = db.scalar(
        select(func.count(Room.id)).where(Room.status == "maintenance")
    ) or 0
    bookable = total_rooms - maintenance

    occupied = db.scalar(
        select(func.count(func.distinct(Booking.room_id)))
        .join(Room, Room.id == Booking.room_id)
        .where(
            Room.status == "available",
            Booking.status.in_(ACTIVE_STATUSES),
            Booking.check_in <= day,
            Booking.check_out > day,
        )
    ) or 0

    if bookable > 0:
        rate = (Decimal(occupied) * 100 / Decimal(bookable)).quantize(Decimal("0.01"))
    else: 
        rate = Decimal("0.00")

    return {
        "report_date": day,
        "total_rooms": total_rooms,
        "maintenance_rooms": maintenance,
        "bookable_rooms": bookable,
        "occupied_rooms": occupied,
        "available_rooms": bookable - occupied,
        "occupancy_rate": rate,
    }

def revenue_between(db: Session, start: date, end: date) -> dict:
    paid_day = cast(func.timezone(REPORT_TZ, Payment.paid_at), Date)
    stmt = (
        select(
            paid_day.label("day"),
            func.sum(Payment.amount),
            func.count(Payment.id),
        )
        .where(Payment.status == "completed", paid_day >= start, paid_day <= end)
        .group_by("day")
        .order_by("day")
    )
    rows = db.execute(stmt).all()
    by_day = [
        {"report_date": r[0], "total": r[1], "payments_count": r[2]} for r in rows
    ]
    return {
        "start_date": start,
        "end_date": end,
        "total_revenue": sum((d["total"] for d in by_day), Decimal("0")),
        "payments_count": sum(d["payments_count"] for d in by_day),
        "by_day": by_day,
    }
