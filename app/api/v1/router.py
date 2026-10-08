from fastapi import APIRouter
from app.api.v1.endpoints import auth, guests, room_types, rooms, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(room_types.router)
api_router.include_router(rooms.router)
api_router.include_router(guests.router)
api_router.include_router(users.router)