
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
    image_url: str | None = None
    amenities: str | None = None

class RoomUpdate(BaseModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=10)
    floor: int | None = Field(default=None, ge=0, le=100)
    status: RoomStatus | None = None
    room_type_id: int | None = None
    image_url: str | None = None
    amenities: str | None = None

class RoomOut(RoomBase):
    id: int
    room_type: RoomTypeOut
    image_url: str | None = None
    amenities: str | None = None
    
    model_config = ConfigDict(from_attributes=True)
