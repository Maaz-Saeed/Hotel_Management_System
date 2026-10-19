from sqlalchemy import select

from app.core.reset import make_reset_token
from app.db.session import Sessionlocal
from app.models.user import User

LOGIN = "/api/v1/auth/login"
BASE = "/api/v1/auth"


def login(client, email, password):
    return client.post(LOGIN, data={"username": email, "password": password})


def test_change_password(client, make_user):
    c = make_user("receptionist")
    token = login(client, c["email"], c["password"]).json()["access_token"]
    h = {"Authorization": "Bearer " + token}
    wrong = client.post(f"{BASE}/change-password", json={"current_password": "wrongpass1", "new_password": "newpass1234"}, headers=h)
    assert wrong.status_code == 400
    ok = client.post(f"{BASE}/change-password", json={"current_password": c["password"], "new_password": "newpass1234"}, headers=h)
    assert ok.status_code == 200
    assert login(client, c["email"], c["password"]).status_code == 401
    assert login(client, c["email"], "newpass1234").status_code == 200


def test_forgot_gives_same_answer_for_known_and_unknown_email(client, make_user):
    c = make_user("manager")
    a = client.post(f"{BASE}/forgot", json={"email": c["email"]})
    b = client.post(f"{BASE}/forgot", json={"email": "nobody@test.com"})
    assert a.status_code == b.status_code == 200
    assert a.json() == b.json()


def test_reset_link_works_once(client, make_user):
    c = make_user("manager")
    with Sessionlocal() as db:
        hashed = db.scalar(select(User.hashed_password).where(User.email == c["email"]))
    token = make_reset_token("staff", c["email"], hashed)
    r = client.post(f"{BASE}/reset", json={"token": token, "new_password": "brandnew123"})
    assert r.status_code == 200
    assert login(client, c["email"], "brandnew123").status_code == 200
    again = client.post(f"{BASE}/reset", json={"token": token, "new_password": "another12345"})
    assert again.status_code == 400


def test_reset_rejects_garbage_and_wrong_kind(client, make_user):
    c = make_user("manager")
    assert client.post(f"{BASE}/reset", json={"token": "x" * 40, "new_password": "brandnew123"}).status_code == 400
    with Sessionlocal() as db:
        hashed = db.scalar(select(User.hashed_password).where(User.email == c["email"]))
    customer_token = make_reset_token("customer", c["email"], hashed)
    assert client.post(f"{BASE}/reset", json={"token": customer_token, "new_password": "brandnew123"}).status_code == 400
