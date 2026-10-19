from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

PHONE = r"^\+?[0-9\- ]{7,20}$"


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
    adults: int = Field(default=1, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    special_requests: str | None = Field(default=None, max_length=500)
    id_type: Literal["CNIC", "Passport", "Other"] | None = None
    id_number: str | None = Field(default=None, min_length=3, max_length=50)
    address: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def check_dates(self):
        if bool(self.id_type) != bool(self.id_number):
            raise ValueError("Give both the ID type and the ID number")
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


class CustomerRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(pattern=PHONE)
    password: str = Field(min_length=8, max_length=72)


class CustomerLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: str
    phone: str


class CustomerToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer: CustomerOut
