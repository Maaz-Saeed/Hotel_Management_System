from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.crud import booking as crud_booking
from app.db.session import get_db
from app.models.user import User
from app.schemas.booking import BookingOut
from app.schemas.report import OccupancyOut, RevenueOut
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ManagerUser = Annotated[User, Depends(require_role("admin", "manager"))]


@router.get("/arrivals", response_model=list[BookingOut])
def arrivals(db: DbSession, user: CurrentUser, day: date | None = None):
    return crud_booking.list_arrivals(db, day or date.today())


@router.get("/departures", response_model=list[BookingOut])
def departures(db: DbSession, user: CurrentUser, day: date | None = None):
    return crud_booking.list_departures(db, day or date.today())


@router.get("/occupancy", response_model=OccupancyOut)
def occupancy(db: DbSession, user: CurrentUser, day: date | None = None):
    return report_service.occupancy_for_day(db, day or date.today())


@router.get("/revenue", response_model=RevenueOut)
def revenue(db: DbSession, manager: ManagerUser, start_date: date, end_date: date):
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")
    if (end_date - start_date).days > 366:
        raise HTTPException(status_code=422, detail="Date range cannot be more than 366 days")
    return report_service.revenue_between(db, start_date, end_date)
