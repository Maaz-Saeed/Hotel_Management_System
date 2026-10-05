from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field
Role = Literal["admin", "receptionist", "manager"]

class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Role = "receptionist"

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: Role | None = None
    is_active: bool | None = None

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    