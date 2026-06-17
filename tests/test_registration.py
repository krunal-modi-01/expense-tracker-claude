import json
import pytest
from werkzeug.security import check_password_hash
from database.db import get_db


VALID_PAYLOAD = {
    "name": "Priya Sharma",
    "email": "priya@example.com",
    "password": "secret123",
    "confirm_password": "secret123",
}


def post_json(client, payload):
    return client.post(
        "/register",
        data=json.dumps(payload),
        content_type="application/json",
    )


# ------------------------------------------------------------------ #
# GET                                                                  #
# ------------------------------------------------------------------ #

def test_register_page_loads(client):
    res = client.get("/register")
    assert res.status_code == 200
    assert b"Create your account" in res.data


# ------------------------------------------------------------------ #
# POST — success                                                       #
# ------------------------------------------------------------------ #

def test_register_success(client):
    res = post_json(client, VALID_PAYLOAD)
    assert res.status_code == 201
    body = res.get_json()
    assert body["success"] is True
    assert body["message"] == "Account created successfully"


def test_register_success_stores_hashed_password(app, client):
    post_json(client, VALID_PAYLOAD)
    with app.app_context():
        conn = get_db()
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (VALID_PAYLOAD["email"],),
        ).fetchone()
        conn.close()
    assert row is not None
    assert check_password_hash(row["password_hash"], VALID_PAYLOAD["password"])


def test_register_success_contains_no_token(client):
    res = post_json(client, VALID_PAYLOAD)
    body = res.get_json()
    assert "token" not in body
    assert "data" not in body


# ------------------------------------------------------------------ #
# POST — duplicate email                                               #
# ------------------------------------------------------------------ #

def test_register_duplicate_email(client):
    post_json(client, VALID_PAYLOAD)
    res = post_json(client, VALID_PAYLOAD)
    assert res.status_code == 409
    body = res.get_json()
    assert "email" in body["errors"]


def test_register_duplicate_email_no_extra_row(app, client):
    post_json(client, VALID_PAYLOAD)
    post_json(client, VALID_PAYLOAD)
    with app.app_context():
        conn = get_db()
        count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?",
            (VALID_PAYLOAD["email"],),
        ).fetchone()[0]
        conn.close()
    assert count == 1


# ------------------------------------------------------------------ #
# POST — validation errors                                             #
# ------------------------------------------------------------------ #

def test_register_empty_name(client):
    payload = {**VALID_PAYLOAD, "name": ""}
    res = post_json(client, payload)
    assert res.status_code == 400
    assert "name" in res.get_json()["errors"]


def test_register_short_password(client):
    payload = {**VALID_PAYLOAD, "password": "abc", "confirm_password": "abc"}
    res = post_json(client, payload)
    assert res.status_code == 400
    assert "password" in res.get_json()["errors"]


def test_register_password_mismatch(client):
    payload = {**VALID_PAYLOAD, "confirm_password": "different"}
    res = post_json(client, payload)
    assert res.status_code == 400
    assert "confirm_password" in res.get_json()["errors"]


def test_register_invalid_email(client):
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}
    res = post_json(client, payload)
    assert res.status_code == 400
    assert "email" in res.get_json()["errors"]


def test_register_all_errors_at_once(client):
    res = post_json(client, {})
    assert res.status_code == 400
    errors = res.get_json()["errors"]
    assert "name" in errors
    assert "email" in errors
    assert "password" in errors
    assert "confirm_password" in errors


# ------------------------------------------------------------------ #
# POST — content type                                                  #
# ------------------------------------------------------------------ #

def test_register_wrong_content_type(client):
    res = client.post(
        "/register",
        data="name=Test&email=test@test.com&password=pass123&confirm_password=pass123",
        content_type="application/x-www-form-urlencoded",
    )
    assert res.status_code == 415
    assert "error" in res.get_json()


# ------------------------------------------------------------------ #
# POST — no session cookie set                                         #
# ------------------------------------------------------------------ #

def test_register_no_session_cookie(client):
    res = post_json(client, VALID_PAYLOAD)
    # Flask only sets the session cookie when session data is written
    assert "session" not in res.headers.get("Set-Cookie", "")
