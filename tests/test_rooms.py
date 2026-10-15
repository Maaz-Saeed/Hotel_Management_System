ROOMS = "/api/v1/rooms"
TYPES = "/api/v1/room-types"


def test_admin_creates_room_with_nested_type(client, admin_headers, room_type):
    r = client.post(
        ROOMS,
        json={"room_number": "101", "floor": 1, "room_type_id": room_type["id"]},
        headers=admin_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "available"
    assert body["room_type"]["name"] == "Single"


def test_duplicate_room_number_rejected(client, admin_headers, room_type, make_room):
    make_room("101")
    r = client.post(
        ROOMS,
        json={"room_number": "101", "floor": 2, "room_type_id": room_type["id"]},
        headers=admin_headers,
    )
    assert r.status_code == 409


def test_room_with_unknown_type_returns_404(client, admin_headers):
    r = client.post(
        ROOMS,
        json={"room_number": "101", "floor": 1, "room_type_id": 999},
        headers=admin_headers,
    )
    assert r.status_code == 404


def test_invalid_status_rejected(client, admin_headers, room_type):
    r = client.post(
        ROOMS,
        json={
            "room_number": "101",
            "floor": 1,
            "status": "broken",
            "room_type_id": room_type["id"],
        },
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_receptionist_cannot_create_room(client, reception_headers, room_type):
    r = client.post(
        ROOMS,
        json={"room_number": "101", "floor": 1, "room_type_id": room_type["id"]},
        headers=reception_headers,
    )
    assert r.status_code == 403


def test_receptionist_can_view_rooms(client, reception_headers, make_room):
    make_room("101")
    r = client.get(ROOMS, headers=reception_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_filter_with_no_match_returns_empty_list(client, admin_headers, make_room):
    make_room("101")
    r = client.get(ROOMS, params={"room_type_id": 999}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_missing_room_returns_404(client, admin_headers):
    assert client.get(f"{ROOMS}/999", headers=admin_headers).status_code == 404


def test_room_type_with_rooms_cannot_be_deleted(client, admin_headers, room_type, make_room):
    make_room("101")
    r = client.delete(f"{TYPES}/{room_type['id']}", headers=admin_headers)
    assert r.status_code == 409


def test_empty_room_type_can_be_deleted(client, admin_headers, room_type):
    r = client.delete(f"{TYPES}/{room_type['id']}", headers=admin_headers)
    assert r.status_code == 204


def test_patch_changes_only_sent_fields(client, admin_headers, make_room):
    room = make_room("101")
    r = client.patch(
        f"{ROOMS}/{room['id']}", json={"status": "maintenance"}, headers=admin_headers
    )
    body = r.json()
    assert r.status_code == 200
    assert body["status"] == "maintenance"
    assert body["room_number"] == "101"
    assert body["floor"] == 1


def test_room_type_name_is_unique_ignoring_case(client, admin_headers, room_type):
    r = client.post(
        TYPES,
        json={"name": "single", "base_price": 100, "capacity": 1},
        headers=admin_headers,
    )
    assert r.status_code == 409
    