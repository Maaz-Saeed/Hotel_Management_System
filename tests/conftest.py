import os
from pathlib import Path

from dotenv import dotenv_values

# 1) Pehle test database ka URL tay karo, app import hone SE PEHLE
ROOT = Path(__file__).resolve().parents[1]
_real_url = dotenv_values(ROOT / ".env")["DATABASE_URL"]
_server_url = _real_url.rsplit("/", 1)[0]
TEST_DB_NAME = "hotel_test_db"
os.environ["DATABASE_URL"] = f"{_server_url}/{TEST_DB_NAME}"

# 2) Ab app import karo (ab woh test database dekhegi)
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import Sessionlocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

# 3) Safety check: asli database par tests kabhi nahi chalenge
assert engine.url.database == TEST_DB_NAME, "Tests must run on the test database only"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    admin = create_engine(f"{_server_url}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB_NAME}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    command.upgrade(cfg, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database():
    yield
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE payments, bookings, rooms, room_types, guests, users "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_user():
    def _make(role="receptionist", email=None, password="password123"):
        email = email or f"{role}@test.com"
        with Sessionlocal() as db:
            db.add(
                User(
                    full_name=f"Test {role}",
                    email=email,
                    hashed_password=hash_password(password),
                    role=role,
                )
            )
            db.commit()
        return {"email": email, "password": password}

    return _make


@pytest.fixture
def auth_headers(client, make_user):
    def _headers(role="admin"):
        creds = make_user(role)
        r = client.post(
            "/api/v1/auth/login",
            data={"username": creds["email"], "password": creds["password"]},
        )
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _headers

@pytest.fixture
def admin_headers(auth_headers):
    return auth_headers("admin")


@pytest.fixture
def reception_headers(auth_headers):
    return auth_headers("receptionist")


@pytest.fixture
def manager_headers(auth_headers):
    return auth_headers("manager")


@pytest.fixture
def room_type(client, admin_headers):
    r = client.post(
        "/api/v1/room-types",
        json={"name": "Single", "base_price": 3000, "capacity": 1},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def make_room(client, admin_headers, room_type):
    def _make(number="101", floor=1, status="available"):
        r = client.post(
            "/api/v1/rooms",
            json={
                "room_number": number,
                "floor": floor,
                "status": status,
                "room_type_id": room_type["id"],
            },
            headers=admin_headers,
        )
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture
def guest(client, admin_headers):
    r = client.post(
        "/api/v1/guests",
        json={
            "full_name": "Ali Khan",
            "phone": "0300-1234567",
            "id_type": "CNIC",
            "id_number": "35202-1234567-1",
        },
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()
