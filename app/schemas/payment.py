from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["cash", "card", "online"]
PaymentStatus = Literal["completed", "refunded"]

class PaymentCreate(BaseModel):
    booking_id: int
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    method: PaymentMethod

class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    methode: PaymentMethod
    status: PaymentStatus
    paid_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BalanceOut(BaseModel):
    booking_id: int
    total_amount: Decimal
    total_paid: Decimal
    balance_due: Decimal
    payment_status: Literal["unpaid", "partial", "paid"]