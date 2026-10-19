from app.db.session import Sessionlocal
from app.models.guest import Guest
from tests.utils import day

BOOKINGS = "/api/v1/bookings"


def book(client, headers, guest_id, room_id, start, end, **extra):
    return client.post(
        BOOKINGS,
        json={"guest_id": guest_id, "room_id": room_id, "check_in": day(start), "check_out": day(end), **extra},
        headers=headers,
    )


def test_booking_saves_guest_counts_and_requests(client, admin_headers, guest, make_room):
    room = make_room("101")
    r = book(client, admin_headers, guest["id"], room["id"], 10, 12, adults=1, children=0, special_requests="Late arrival")
    assert r.status_code == 201
    body = r.json()
    assert body["adults"] == 1 and body["children"] == 0
    assert body["special_requests"] == "Late arrival"


def test_counts_default_to_one_adult(client, admin_headers, guest, make_room):
    room = make_room("101")
    body = book(client, admin_headers, guest["id"], room["id"], 10, 12).json()
    assert body["adults"] == 1 and body["children"] == 0


def test_too_many_guests_rejected(client, admin_headers, guest, make_room):
    room = make_room("101")  # the Single room sleeps 1
    r = book(client, admin_headers, guest["id"], room["id"], 10, 12, adults=2)
    assert r.status_code == 422
    assert "sleeps at most" in r.json()["detail"]


def test_check_in_needs_guest_id(client, admin_headers, make_room):
    room = make_room("101")
    with Sessionlocal() as db:
        g = Guest(full_name="Online Guest", email="online@test.com", phone="0300-1234567")
        db.add(g)
        db.commit()
        guest_id = g.id
    booking = book(client, admin_headers, guest_id, room["id"], 0, 2).json()
    url = f"{BOOKINGS}/{booking['id']}/check-in"
    blocked = client.post(url, headers=admin_headers)
    assert blocked.status_code == 409
    assert "ID" in blocked.json()["detail"]
    client.patch(f"/api/v1/guests/{guest_id}", json={"id_type": "CNIC", "id_number": "35202-7654321-9"}, headers=admin_headers)
    assert client.post(url, headers=admin_headers).status_code == 200
