
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.room_type import RoomTypeOut
RoomStatus = Literal["available", "maintenance"]

class RoomBase(BaseModel):
    room_number: str = Field(min_length=1, max_length=10)
    floor: int = Field(ge=0, le=100)
    status: RoomStatus = "available"

class RoomCreate(RoomBase):
    room_type_id: int 

class RoomUpdate(BaseModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=10)
    floor: int | None = Field(default=None, ge=0, le=100)
    staus: RoomStatus | None = None
    room_type_id: int | None = None

class RoomOut(RoomBase):
    id: int
    room_type: RoomTypeOut

    model_config = ConfigDict(from_attributes=True)
