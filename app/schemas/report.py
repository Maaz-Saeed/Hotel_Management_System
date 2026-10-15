from datetime import date
from decimal import Decimal 

from pydantic import BaseModel

class OccupancyOut(BaseModel):
    report_date: date
    total_rooms: int
    maintenance_rooms: int
    bookable_rooms: int
    occupied_rooms: int
    available_rooms: int
    occupancy_rate: Decimal

class RevenueDay(BaseModel):
    report_date: date
    total: Decimal
    payments_count: int

class RevenueOut(BaseModel):
    start_date: date
    end_date: date
    total_revenue: Decimal
    payments_count: int
    by_day: list[RevenueDay]
    