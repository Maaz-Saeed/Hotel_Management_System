from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class RoomTypeBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    base_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    capacity: int = Field(default=1, ge=1, le=10)
    description: str | None = Field(default=None, max_length=255)

class RoomTypeCreate(RoomTypeBase):
    pass

class RoomTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    base_price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    capacity: int | None = Field(default=None, ge=1, le=10)
    description: str | None = Field(default=None, max_length=255)

class RoomTypeOut(RoomTypeBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
    