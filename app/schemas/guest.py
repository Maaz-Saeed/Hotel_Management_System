from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

IdType = Literal["CNIC", "Passport", "Other"]

class GuestBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str =Field(pattern=r"^\+?[0-9\- ]{7,20}$")
    id_type: IdType
    id_number: str = Field(min_length=3, max_length=50)
    address: str | None = Field(default=None, max_length=255)

class GuestCreate(GuestBase):
    pass 

class GuestUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9\- ]{7,20}$")
    id_type: IdType | None = None
    id_number: str | None = Field(default=None, min_length=3, max_length=50)
    address: str | None = Field(default=None, max_length=255)

class GuestOut(GuestBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    