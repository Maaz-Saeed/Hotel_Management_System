from decimal import Decimal

import pytest

from tests.utils import day

PAYMENTS = "/api/v1/payments"
BOOKINGS = "/api/v1/bookings"


@pytest.fixture
def booking(client, admin_headers, guest, make_room):
    room = make_room("101")
    r = client.post(
        BOOKINGS,
        json={
            "guest_id": guest["id"],
            "room_id": room["id"],
            "check_in": day(10),
            "check_out": day(13),
        },
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def pay(client, headers, booking, amount, method="cash"):
    return client.post(
        PAYMENTS,
        json={"booking_id": booking["id"], "amount": amount, "method": method},
        headers=headers,
    )


def balance(client, headers, booking):
    r = client.get(f"{BOOKINGS}/{booking['id']}/balance", headers=headers)
    assert r.status_code == 200
    return r.json()


def test_balance_starts_unpaid(client, admin_headers, booking):
    b = balance(client, admin_headers, booking)
    assert Decimal(b["total_amount"]) == Decimal("9000")
    assert Decimal(b["total_paid"]) == 0
    assert Decimal(b["balance_due"]) == Decimal("9000")
    assert b["payment_status"] == "unpaid"


def test_partial_then_full_payment(client, admin_headers, booking):
    assert pay(client, admin_headers, booking, 3000).status_code == 201
    b = balance(client, admin_headers, booking)
    assert Decimal(b["balance_due"]) == Decimal("6000")
    assert b["payment_status"] == "partial"

    r = pay(client, admin_headers, booking, 7000)
    assert r.status_code == 409
    assert "more than the balance due" in r.json()["detail"]

    assert pay(client, admin_headers, booking, 6000, "card").status_code == 201
    b = balance(client, admin_headers, booking)
    assert Decimal(b["balance_due"]) == 0
    assert b["payment_status"] == "paid"

    assert pay(client, admin_headers, booking, 1).status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": -500, "method": "cash"},
        {"amount": 100, "method": "gold"},
        {"amount": "100.555", "method": "cash"},
    ],
)
def test_invalid_payment_rejected(client, admin_headers, booking, payload):
    r = client.post(
        PAYMENTS, json={"booking_id": booking["id"], **payload}, headers=admin_headers
    )
    assert r.status_code == 422


def test_cancelled_booking_cannot_take_payment(client, admin_headers, booking):
    client.post(f"{BOOKINGS}/{booking['id']}/cancel", headers=admin_headers)
    assert pay(client, admin_headers, booking, 1000).status_code == 409


def test_unknown_booking_returns_404(client, admin_headers):
    assert pay(client, admin_headers, {"id": 999}, 1000).status_code == 404


def test_payments_cannot_be_deleted(client, admin_headers, booking):
    payment = pay(client, admin_headers, booking, 1000).json()
    r = client.delete(f"{PAYMENTS}/{payment['id']}", headers=admin_headers)
    assert r.status_code == 405


def test_manager_can_view_but_not_take_payment(client, admin_headers, manager_headers, booking):
    assert pay(client, manager_headers, booking, 1000).status_code == 403
    assert client.get(PAYMENTS, headers=manager_headers).status_code == 200


def test_list_payments_filters_by_booking(client, admin_headers, booking):
    pay(client, admin_headers, booking, 1000)
    pay(client, admin_headers, booking, 2000)
    r = client.get(PAYMENTS, params={"booking_id": booking["id"]}, headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()) == 2
    