from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator, EmailStr


class PublicRoomType(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    base_price: float
    capacity: int
    description: str | None = None
    image_url: str | None = None
    amenities: str | None = None
    available_rooms: int | None = None
    nights: int | None = None
    total: float | None = None


class OnlineBookingIn(BaseModel):
    room_type_id: int
    check_in: date
    check_out: date
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(pattern=r"^\+?[0-9\- ]{7,20}$")

    @model_validator(mode="after")
    def check_dates(self):
        if self.check_in < date.today():
            raise ValueError("Check-in cannot be in the past")
        if not 1 <= (self.check_out - self.check_in).days <= 30:
            raise ValueError("Stay must be between 1 and 30 nights")
        return self


class OnlineBookingOut(BaseModel):
    reference: str
    status: str
    room_type: str
    room_number: str
    check_in: date
    check_out: date
    total_amount: float
