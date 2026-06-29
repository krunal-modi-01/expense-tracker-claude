import json
import pytest
from werkzeug.security import generate_password_hash
from database.db import get_db, create_user


USER = {
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


def get_token(client):
    res = post_json(client, "/login", {"email": USER["email"], "password": USER["password"]})
    return res.get_json()["data"]["token"]


def auth_get(client, path, token):
    return client.get(path, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture(autouse=True)
def seed_user(app):
    with app.app_context():
        create_user(
            USER["name"],
            USER["email"],
            generate_password_hash(USER["password"]),
        )


# ------------------------------------------------------------------ #
# GET /profile — page shell                                            #
# ------------------------------------------------------------------ #

def test_profile_page_loads(client):
    res = client.get("/profile")
    assert res.status_code == 200
    assert b"profile" in res.data.lower()


# ------------------------------------------------------------------ #
# GET /api/profile — success                                           #
# ------------------------------------------------------------------ #

def test_api_profile_success(client):
    token = get_token(client)
    res = auth_get(client, "/api/profile", token)
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert "user" in body["data"]
    assert "stats" in body["data"]


def test_api_profile_user_fields(client):
    token = get_token(client)
    res = auth_get(client, "/api/profile", token)
    user = res.get_json()["data"]["user"]
    assert user["name"] == USER["name"]
    assert user["email"] == USER["email"]
    assert "id" in user
    assert "member_since" in user
    assert len(user["member_since"]) == 10  # YYYY-MM-DD


def test_api_profile_stats_keys(client):
    token = get_token(client)
    res = auth_get(client, "/api/profile", token)
    stats = res.get_json()["data"]["stats"]
    assert "total_expenses" in stats
    assert "total_amount" in stats
    assert isinstance(stats["by_category"], list)


def test_api_profile_stats_with_expenses(app, client):
    with app.app_context():
        conn = get_db()
        user_id = conn.execute(
            "SELECT id FROM users WHERE email = ?", (USER["email"],)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO expense (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (user_id, 100.0, "Food", "2026-06-01"),
        )
        conn.execute(
            "INSERT INTO expense (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (user_id, 50.0, "Transport", "2026-06-02"),
        )
        conn.commit()
        conn.close()

    token = get_token(client)
    res = auth_get(client, "/api/profile", token)
    stats = res.get_json()["data"]["stats"]
    assert stats["total_expenses"] == 2
    assert abs(stats["total_amount"] - 150.0) < 0.01
    assert len(stats["by_category"]) == 2


# ------------------------------------------------------------------ #
# GET /api/profile — auth errors                                       #
# ------------------------------------------------------------------ #

def test_api_profile_no_auth_header(client):
    res = client.get("/api/profile")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Authentication required"


def test_api_profile_invalid_token(client):
    res = auth_get(client, "/api/profile", "header.tampered.signature")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid or expired token"


def test_api_profile_malformed_bearer(client):
    res = client.get("/api/profile", headers={"Authorization": "Bearer "})
    assert res.status_code == 401
