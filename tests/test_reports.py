from decimal import Decimal

from tests.utils import day

BOOKINGS = "/api/v1/bookings"
REPORTS = "/api/v1/reports"


def book(client, headers, guest, room, start, end):
    r = client.post(
        BOOKINGS,
        json={
            "guest_id": guest["id"],
            "room_id": room["id"],
            "check_in": day(start),
            "check_out": day(end),
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_occupancy_numbers(client, admin_headers, guest, make_room):
    room = make_room("101")
    make_room("102")
    make_room("103", status="maintenance")
    book(client, admin_headers, guest, room, 10, 12)

    r = client.get(f"{REPORTS}/occupancy", params={"day": day(10)}, headers=admin_headers)
    body = r.json()
    assert r.status_code == 200
    assert body["total_rooms"] == 3
    assert body["maintenance_rooms"] == 1
    assert body["bookable_rooms"] == 2
    assert body["occupied_rooms"] == 1
    assert body["available_rooms"] == 1
    assert Decimal(body["occupancy_rate"]) == Decimal("50.00")

    r = client.get(f"{REPORTS}/occupancy", params={"day": day(12)}, headers=admin_headers)
    assert r.json()["occupied_rooms"] == 0


def test_arrivals_exclude_cancelled(client, admin_headers, guest, make_room):
    room = make_room("101")
    booking = book(client, admin_headers, guest, room, 5, 7)
    r = client.get(f"{REPORTS}/arrivals", params={"day": day(5)}, headers=admin_headers)
    assert [b["id"] for b in r.json()] == [booking["id"]]

    client.post(f"{BOOKINGS}/{booking['id']}/cancel", headers=admin_headers)
    r = client.get(f"{REPORTS}/arrivals", params={"day": day(5)}, headers=admin_headers)
    assert r.json() == []


def test_departures_list_checked_in_guest(client, admin_headers, guest, make_room):
    room = make_room("101")
    booking = book(client, admin_headers, guest, room, 0, 2)
    client.post(f"{BOOKINGS}/{booking['id']}/check-in", headers=admin_headers)
    r = client.get(f"{REPORTS}/departures", params={"day": day(2)}, headers=admin_headers)
    assert [b["id"] for b in r.json()] == [booking["id"]]


def test_revenue_counts_payments_not_booking_totals(client, admin_headers, guest, make_room):
    room = make_room("101")
    booking = book(client, admin_headers, guest, room, 10, 13)
    client.post(
        "/api/v1/payments",
        json={"booking_id": booking["id"], "amount": 3000, "method": "cash"},
        headers=admin_headers,
    )
    r = client.get(
        f"{REPORTS}/revenue",
        params={"start_date": day(-1), "end_date": day(1)},
        headers=admin_headers,
    )
    body = r.json()
    assert r.status_code == 200
    assert Decimal(body["total_revenue"]) == Decimal("3000")
    assert body["payments_count"] == 1
    assert len(body["by_day"]) == 1


def test_revenue_is_for_admin_and_manager_only(client, reception_headers, manager_headers):
    params = {"start_date": day(-1), "end_date": day(1)}
    assert client.get(f"{REPORTS}/revenue", params=params, headers=reception_headers).status_code == 403
    assert client.get(f"{REPORTS}/revenue", params=params, headers=manager_headers).status_code == 200


def test_revenue_end_before_start_rejected(client, admin_headers):
    r = client.get(
        f"{REPORTS}/revenue",
        params={"start_date": day(5), "end_date": day(1)},
        headers=admin_headers,
    )
    assert r.status_code == 422
    