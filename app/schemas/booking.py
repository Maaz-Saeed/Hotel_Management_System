from datetime import date, datetime
from decimal import Decimal 
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.guest import GuestOut
from app.schemas.room import RoomOut

BookingStatus = Literal["reserved", "checked_in", "checked_out", "canceled"]

class BookingCreate(BaseModel):
    guest_id: int
    room_id: int
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.check_in < date.today():
            raise ValueError("chenk_in cannot be in past")
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self

class BookingOut(BaseModel):
    id: int 
    check_in: date
    check_out: date
    status: BookingStatus
    total_amount: Decimal
    created_by: int
    created_at: datetime
    guest: GuestOut
    room: RoomOut

    model_config = ConfigDict(from_attributes=True)
