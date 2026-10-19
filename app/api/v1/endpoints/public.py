import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.booking import Booking
from app.models.customer import Customer
from app.models.guest import Guest
from app.models.room_type import RoomType
from app.schemas.public import (
    CustomerLogin, CustomerOut, CustomerRegister, CustomerToken,
    OnlineBookingIn, OnlineBookingOut, PublicRoomType,
)
from app.services.booking_service import find_available_rooms

router = APIRouter(prefix="/public", tags=["Public (guests)"])
bearer = HTTPBearer(auto_error=False)
PREFIX = "c:"  # customer tokens are marked so they can never work as staff tokens


def current_customer(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> Customer:
    sub = decode_access_token(creds.credentials) if creds else None
    customer = None
    if sub and sub.startswith(PREFIX):
        customer = db.scalar(select(Customer).where(Customer.email == sub[len(PREFIX):]))
    if customer is None:
        raise HTTPException(401, "Please sign in to continue", headers={"WWW-Authenticate": "Bearer"})
    return customer


def token_for(customer: Customer) -> CustomerToken:
    return CustomerToken(
        access_token=create_access_token(PREFIX + customer.email),
        customer=CustomerOut.model_validate(customer),
    )


def to_out(b: Booking) -> OnlineBookingOut:
    return OnlineBookingOut(
        reference=b.reference, status=b.status, room_type=b.room.room_type.name,
        room_number=b.room.room_number, check_in=b.check_in,
        check_out=b.check_out, total_amount=b.total_amount,
    )


def find_booking(db: Session, reference: str, email: str) -> Booking:
    b = db.scalar(
        select(Booking).join(Guest, Booking.guest_id == Guest.id)
        .where(Booking.reference == reference.upper(), func.lower(Guest.email) == email.lower())
    )
    if not b:
        raise HTTPException(404, "No booking found for that reference and email")
    return b


@router.post("/auth/register", response_model=CustomerToken, status_code=201)
def register(data: CustomerRegister, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(Customer).where(Customer.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    customer = Customer(full_name=data.full_name, email=email, phone=data.phone,
                        hashed_password=hash_password(data.password))
    db.add(customer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists")
    db.refresh(customer)
    return token_for(customer)


@router.post("/auth/login", response_model=CustomerToken)
def login(data: CustomerLogin, db: Session = Depends(get_db)):
    customer = db.scalar(select(Customer).where(Customer.email == data.email.lower()))
    if customer is None or not verify_password(data.password, customer.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    return token_for(customer)


@router.get("/auth/me", response_model=CustomerOut)
def me(customer: Customer = Depends(current_customer)):
    return customer


@router.get("/room-types", response_model=list[PublicRoomType])
def list_room_types(check_in: date | None = None, check_out: date | None = None,
                    db: Session = Depends(get_db)):
    if bool(check_in) != bool(check_out):
        raise HTTPException(422, "Send both check_in and check_out")
    if check_in and (check_in < date.today() or check_out <= check_in):
        raise HTTPException(422, "Invalid dates")
    out = []
    for rt in db.scalars(select(RoomType).order_by(RoomType.base_price)):
        item = PublicRoomType.model_validate(rt)
        if check_in:
            item.available_rooms = len(find_available_rooms(db, check_in, check_out, rt.id))
            item.nights = (check_out - check_in).days
            item.total = float(rt.base_price) * item.nights
        out.append(item)
    return out


@router.post("/bookings", response_model=OnlineBookingOut, status_code=201)
def create_online_booking(data: OnlineBookingIn, db: Session = Depends(get_db),
                          customer: Customer = Depends(current_customer)):
    rt = db.get(RoomType, data.room_type_id)
    if not rt:
        raise HTTPException(404, "Room type not found")
    if data.adults + data.children > rt.capacity:
        raise HTTPException(422, f"This room type sleeps at most {rt.capacity} guest(s)")
    nights = (data.check_out - data.check_in).days
    guest = db.scalar(select(Guest).where(func.lower(Guest.email) == customer.email))
    if not guest:
        guest = Guest(full_name=customer.full_name, email=customer.email, phone=customer.phone)
        db.add(guest)
        db.flush()
    if data.id_number and not guest.id_number:
        clash = db.scalar(select(Guest).where(Guest.id_type == data.id_type, Guest.id_number == data.id_number, Guest.id != guest.id))
        if clash:
            raise HTTPException(409, "This ID is already registered with another guest. Please contact reception.")
        guest.id_type, guest.id_number = data.id_type, data.id_number
    if data.address and not guest.address:
        guest.address = data.address
    for room in find_available_rooms(db, data.check_in, data.check_out, rt.id):
        booking = Booking(
            guest_id=guest.id, room_id=room.id, created_by=None, source="online",
            check_in=data.check_in, check_out=data.check_out, status="reserved",
            adults=data.adults, children=data.children, special_requests=data.special_requests,
            total_amount=rt.base_price * nights, reference="HMS-" + secrets.token_hex(3).upper(),
        )
        try:
            with db.begin_nested():
                db.add(booking)
        except IntegrityError:
            continue  # another request took this room; try the next one
        db.commit()
        db.refresh(booking)
        return to_out(booking)
    db.rollback()
    raise HTTPException(409, "No rooms of this type are free for those dates")


@router.get("/my-bookings", response_model=list[OnlineBookingOut])
def my_bookings(db: Session = Depends(get_db), customer: Customer = Depends(current_customer)):
    rows = db.scalars(
        select(Booking).join(Guest, Booking.guest_id == Guest.id)
        .where(func.lower(Guest.email) == customer.email).order_by(Booking.id.desc())
    ).all()
    return [to_out(b) for b in rows]


@router.post("/my-bookings/{reference}/cancel", response_model=OnlineBookingOut)
def cancel_my_booking(reference: str, db: Session = Depends(get_db),
                      customer: Customer = Depends(current_customer)):
    b = find_booking(db, reference, customer.email)
    if b.status != "reserved":
        raise HTTPException(409, "Only reservations that have not checked in can be cancelled")
    b.status = "cancelled"
    db.commit()
    return to_out(b)


@router.get("/bookings/{reference}", response_model=OnlineBookingOut)
def lookup_booking(reference: str, email: str, db: Session = Depends(get_db)):
    return to_out(find_booking(db, reference, email))


@router.post("/bookings/{reference}/cancel", response_model=OnlineBookingOut)
def cancel_booking(reference: str, email: str, db: Session = Depends(get_db)):
    b = find_booking(db, reference, email)
    if b.status != "reserved":
        raise HTTPException(409, "Only reservations that have not checked in can be cancelled")
    b.status = "cancelled"
    db.commit()
    return to_out(b)
