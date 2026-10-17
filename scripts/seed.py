from decimal import Decimal

from sqlalchemy import select

from app.db.session import Sessionlocal
from app.models.room import Room
from app.models.room_type import RoomType

ROOM_TYPES = [
    ("Single", Decimal("3000"), 1, "One guest"),
    ("Double", Decimal("5000"), 2, "Two guests"),
    ("Suite", Decimal("9000"), 4, "Family suite"),
]
ROOMS = [
    ("101", 1, "Single"),
    ("102", 1, "Single"),
    ("201", 2, "Double"),
    ("202", 2, "Double"),
    ("301", 3, "Suite"),
]


def main():
    with Sessionlocal() as db:
        types = {}
        for name, price, capacity, description in ROOM_TYPES:
            room_type = db.scalar(select(RoomType).where(RoomType.name == name))
            if room_type is None:
                room_type = RoomType(
                    name=name, base_price=price, capacity=capacity, description=description
                )
                db.add(room_type)
                db.flush()
            types[name] = room_type

        for number, floor, type_name in ROOMS:
            exists = db.scalar(select(Room).where(Room.room_number == number))
            if exists is None:
                db.add(
                    Room(
                        room_number=number,
                        floor=floor,
                        status="available",
                        room_type_id=types[type_name].id,
                    )
                )
        db.commit()
        print("Seed complete")


if __name__ == "__main__":
    main()
