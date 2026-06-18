import json
import pytest
from werkzeug.security import generate_password_hash
from database.db import get_db, create_user
from database.auth import decode_jwt


REGISTERED_USER = {
    "name": "Priya Sharma",
    "email": "priya@example.com",
    "password": "secret123",
}


def post_json(client, path, payload):
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
    )


@pytest.fixture(autouse=True)
def seed_user(app):
    with app.app_context():
        create_user(
            REGISTERED_USER["name"],
            REGISTERED_USER["email"],
            generate_password_hash(REGISTERED_USER["password"]),
        )


# ------------------------------------------------------------------ #
# GET /login                                                           #
# ------------------------------------------------------------------ #

def test_login_page_loads(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert b"Welcome back" in res.data


# ------------------------------------------------------------------ #
# POST /login — success                                                #
# ------------------------------------------------------------------ #

def test_login_success(client):
    res = post_json(client, "/login", {"email": REGISTERED_USER["email"], "password": REGISTERED_USER["password"]})
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert "token" in body["data"]
    assert body["data"]["user"]["email"] == REGISTERED_USER["email"]
    assert "id" in body["data"]["user"]
    assert "name" in body["data"]["user"]


def test_login_token_is_valid_jwt(app, client):
    res = post_json(client, "/login", {"email": REGISTERED_USER["email"], "password": REGISTERED_USER["password"]})
    token = res.get_json()["data"]["token"]
    payload = decode_jwt(token, app.secret_key)
    assert payload["email"] == REGISTERED_USER["email"]
    assert payload["name"] == REGISTERED_USER["name"]
    assert "sub" in payload
    assert "iat" in payload


# ------------------------------------------------------------------ #
# POST /login — authentication errors                                  #
# ------------------------------------------------------------------ #

def test_login_wrong_password(client):
    res = post_json(client, "/login", {"email": REGISTERED_USER["email"], "password": "wrongpass"})
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"


def test_login_unknown_email(client):
    res = post_json(client, "/login", {"email": "nobody@example.com", "password": "secret123"})
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"


def test_login_wrong_and_unknown_return_same_message(client):
    res_wrong_pw = post_json(client, "/login", {"email": REGISTERED_USER["email"], "password": "bad"})
    res_unknown = post_json(client, "/login", {"email": "nobody@example.com", "password": "bad"})
    assert res_wrong_pw.get_json()["error"] == res_unknown.get_json()["error"]


# ------------------------------------------------------------------ #
# POST /login — validation errors                                      #
# ------------------------------------------------------------------ #

def test_login_missing_email(client):
    res = post_json(client, "/login", {"password": "secret123"})
    assert res.status_code == 400
    assert "email" in res.get_json()["errors"]


def test_login_missing_password(client):
    res = post_json(client, "/login", {"email": REGISTERED_USER["email"]})
    assert res.status_code == 400
    assert "password" in res.get_json()["errors"]


def test_login_all_errors_at_once(client):
    res = post_json(client, "/login", {})
    assert res.status_code == 400
    errors = res.get_json()["errors"]
    assert "email" in errors
    assert "password" in errors


# ------------------------------------------------------------------ #
# POST /login — content type                                           #
# ------------------------------------------------------------------ #

def test_login_wrong_content_type(client):
    res = client.post(
        "/login",
        data="email=test@test.com&password=secret123",
        content_type="application/x-www-form-urlencoded",
    )
    assert res.status_code == 415
    assert "error" in res.get_json()


# ------------------------------------------------------------------ #
# POST /login — no session cookie                                      #
# ------------------------------------------------------------------ #

def test_login_no_session_cookie(client):
    res = post_json(client, "/login", {"email": REGISTERED_USER["email"], "password": REGISTERED_USER["password"]})
    assert "session" not in res.headers.get("Set-Cookie", "")


# ------------------------------------------------------------------ #
# GET /logout                                                          #
# ------------------------------------------------------------------ #

def test_logout_redirects_to_landing(client):
    res = client.get("/logout")
    assert res.status_code == 302
    assert res.headers["Location"] == "/"
