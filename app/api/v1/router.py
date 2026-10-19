from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    bookings,
    guests,
    payments,
    reports,
    room_types,
    rooms,
    users,
    public,
    password,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(room_types.router)
api_router.include_router(rooms.router)
api_router.include_router(guests.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
api_router.include_router(reports.router)
api_router.include_router(public.router)
api_router.include_router(password.router)
