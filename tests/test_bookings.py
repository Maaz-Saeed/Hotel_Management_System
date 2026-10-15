from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.booking import Booking
from app.models.user import User
from tests.utils import day

BOOKINGS = "/api/v1/bookings"
ROOMS = "/api/v1/rooms"
GUESTS = "/api/v1/guests"


def book(client, headers, guest, room, start, end):
    return client.post(
        BOOKINGS,
        json={
            "guest_id": guest["id"],
            "room_id": room["id"],
            "check_in": day(start),
            "check_out": day(end),
        },
        headers=headers,
    )


def available_ids(client, headers, start, end):
    r = client.get(
        f"{ROOMS}/available",
        params={"check_in": day(start), "check_out": day(end)},
        headers=headers,
    )
    assert r.status_code == 200
    return [room["id"] for room in r.json()]


def test_total_is_nights_times_price(client, admin_headers, guest, make_room):
    room = make_room("101")
    r = book(client, admin_headers, guest, room, 10, 13)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "reserved"
    assert Decimal(body["total_amount"]) == Decimal("9000")


def test_same_dates_rejected(client, admin_headers, guest, make_room):
    room = make_room("101")
    assert book(client, admin_headers, guest, room, 10, 13).status_code == 201
    assert book(client, admin_headers, guest, room, 10, 13).status_code == 409


def test_partial_overlap_rejected(client, admin_headers, guest, make_room):
    room = make_room("101")
    book(client, admin_headers, guest, room, 10, 13)
    assert book(client, admin_headers, guest, room, 12, 15).status_code == 409


def test_checkout_day_can_be_booked_by_next_guest(client, admin_headers, guest, make_room):
    room = make_room("101")
    assert book(client, admin_headers, guest, room, 10, 13).status_code == 201
    assert book(client, admin_headers, guest, room, 13, 15).status_code == 201


def test_maintenance_room_cannot_be_booked(client, admin_headers, guest, make_room):
    room = make_room("101", status="maintenance")
    assert book(client, admin_headers, guest, room, 10, 13).status_code == 409


def test_unknown_guest_returns_404(client, admin_headers, make_room):
    room = make_room("101")
    r = book(client, admin_headers, {"id": 999}, room, 10, 13)
    assert r.status_code == 404


def test_unknown_room_returns_404(client, admin_headers, guest):
    r = book(client, admin_headers, guest, {"id": 999}, 10, 13)
    assert r.status_code == 404


def test_past_check_in_rejected(client, admin_headers, guest, make_room):
    room = make_room("101")
    assert book(client, admin_headers, guest, room, -5, -2).status_code == 422


def test_check_out_before_check_in_rejected(client, admin_headers, guest, make_room):
    room = make_room("101")
    assert book(client, admin_headers, guest, room, 13, 10).status_code == 422


def test_available_excludes_booked_room(client, admin_headers, guest, make_room):
    room_a = make_room("101")
    room_b = make_room("102")
    book(client, admin_headers, guest, room_a, 10, 13)
    ids = available_ids(client, admin_headers, 10, 13)
    assert room_b["id"] in ids
    assert room_a["id"] not in ids


def test_cancel_frees_the_room(client, admin_headers, guest, make_room):
    room = make_room("101")
    booking = book(client, admin_headers, guest, room, 10, 13).json()
    r = client.post(f"{BOOKINGS}/{booking['id']}/cancel", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    assert room["id"] in available_ids(client, admin_headers, 10, 13)
    assert book(client, admin_headers, guest, room, 10, 13).status_code == 201


def test_cannot_check_in_before_check_in_date(client, admin_headers, guest, make_room):
    room = make_room("101")
    booking = book(client, admin_headers, guest, room, 10, 12).json()
    r = client.post(f"{BOOKINGS}/{booking['id']}/check-in", headers=admin_headers)
    assert r.status_code == 409
    assert "before the check-in date" in r.json()["detail"]


def test_full_check_in_check_out_flow(client, admin_headers, guest, make_room):
    room = make_room("101")
    booking = book(client, admin_headers, guest, room, 0, 2).json()
    base = f"{BOOKINGS}/{booking['id']}"

    r = client.post(f"{base}/check-in", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "checked_in"
    assert client.post(f"{base}/check-in", headers=admin_headers).status_code == 409
    assert client.post(f"{base}/cancel", headers=admin_headers).status_code == 409

    r = client.post(f"{base}/check-out", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "checked_out"
    assert client.post(f"{base}/check-out", headers=admin_headers).status_code == 409
    assert room["id"] in available_ids(client, admin_headers, 0, 2)


def test_guest_with_bookings_cannot_be_deleted(client, admin_headers, guest, make_room):
    room = make_room("101")
    book(client, admin_headers, guest, room, 10, 13)
    r = client.delete(f"{GUESTS}/{guest['id']}", headers=admin_headers)
    assert r.status_code == 409


def test_room_with_bookings_cannot_be_deleted(client, admin_headers, guest, make_room):
    room = make_room("101")
    book(client, admin_headers, guest, room, 10, 13)
    r = client.delete(f"{ROOMS}/{room['id']}", headers=admin_headers)
    assert r.status_code == 409


def test_manager_can_view_but_not_cancel(client, admin_headers, manager_headers, guest, make_room):
    room = make_room("101")
    booking = book(client, admin_headers, guest, room, 10, 13).json()
    assert client.get(BOOKINGS, headers=manager_headers).status_code == 200
    r = client.post(f"{BOOKINGS}/{booking['id']}/cancel", headers=manager_headers)
    assert r.status_code == 403


def test_database_blocks_overlap_even_without_the_code_check(
    client, admin_headers, guest, make_room
):
    room = make_room("101")
    assert book(client, admin_headers, guest, room, 10, 13).status_code == 201
    with SessionLocal() as db:
        user_id = db.scalar(select(User.id))
        db.add(
            Booking(
                guest_id=guest["id"],
                room_id=room["id"],
                created_by=user_id,
                check_in=date.today() + timedelta(days=11),
                check_out=date.today() + timedelta(days=12),
                status="reserved",
                total_amount=0,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
            