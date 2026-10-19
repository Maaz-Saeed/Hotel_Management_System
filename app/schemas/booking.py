from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.guest import GuestOut
from app.schemas.room import RoomOut

BookingStatus = Literal["reserved", "checked_in", "checked_out", "cancelled"]


class BookingCreate(BaseModel):
    guest_id: int
    room_id: int
    check_in: date
    check_out: date
    adults: int = Field(default=1, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    special_requests: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_dates(self):
        if self.check_in < date.today():
            raise ValueError("check_in cannot be in the past")
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class BookingOut(BaseModel):
    id: int
    check_in: date
    check_out: date
    status: BookingStatus
    total_amount: Decimal
    created_by: int | None = None
    created_at: datetime
    adults: int = 1
    children: int = 0
    special_requests: str | None = None
    guest: GuestOut
    room: RoomOut

    model_config = ConfigDict(from_attributes=True)
