LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


def test_login_success(client, make_user):
    creds = make_user("admin")
    r = client.post(LOGIN, data={"username": creds["email"], "password": creds["password"]})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_wrong_password_and_wrong_email_give_same_message(client, make_user):
    creds = make_user("admin")
    wrong_password = client.post(
        LOGIN, data={"username": creds["email"], "password": "wrongpass1"}
    )
    wrong_email = client.post(
        LOGIN, data={"username": "nobody@test.com", "password": "password123"}
    )
    assert wrong_password.status_code == 401
    assert wrong_email.status_code == 401
    assert wrong_password.json()["detail"] == wrong_email.json()["detail"]


def test_me_requires_login(client):
    assert client.get(ME).status_code == 401


def test_me_hides_password_hash(client, auth_headers):
    r = client.get(ME, headers=auth_headers("admin"))
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    assert "hashed_password" not in r.json()


def test_tampered_token_is_rejected(client, auth_headers):
    token = auth_headers("admin")["Authorization"]
    bad = {"Authorization": token[:-3] + "abc"}
    assert client.get(ME, headers=bad).status_code == 401


def test_receptionist_cannot_list_users(client, auth_headers):
    r = client.get("/api/v1/users", headers=auth_headers("receptionist"))
    assert r.status_code == 403


def test_admin_can_list_users(client, auth_headers):
    r = client.get("/api/v1/users", headers=auth_headers("admin"))
    assert r.status_code == 200
    assert len(r.json()) == 1