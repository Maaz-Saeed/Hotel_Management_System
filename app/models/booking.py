from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Numeric, ForeignKey, CheckConstraint, func
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="ck_booking_dates"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)

    guest_id: Mapped[int] = mapped_column(ForeignKey("guests.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(20), default="reserved")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10,2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    guest: Mapped["Guest"] = relationship()
    room: Mapped["Room"] = relationship()
    created_by_user: Mapped["User"] = relationship()