import sqlite3
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email, get_user_by_id, get_expense_summary
from database.auth import sign_jwt, decode_jwt

app = Flask(__name__)
app.secret_key = "dev-secret-key-spendly-change-in-production"


def _get_jwt_payload():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, "Authentication required"
    try:
        return decode_jwt(auth[7:], app.secret_key), None
    except ValueError:
        return None, "Invalid or expired token"


def _validate_registration(data):
    errors = {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    confirm = data.get("confirm_password") or ""

    if not name:
        errors["name"] = "Name is required"
    elif len(name) > 100:
        errors["name"] = "Name must be 100 characters or fewer"

    if not email:
        errors["email"] = "Email is required"
    elif "@" not in email:
        errors["email"] = "Enter a valid email address"
    elif len(email) > 254:
        errors["email"] = "Email must be 254 characters or fewer"

    if not password:
        errors["password"] = "Password is required"
    elif len(password) < 6:
        errors["password"] = "Password must be at least 6 characters"
    elif len(password) > 128:
        errors["password"] = "Password must be 128 characters or fewer"

    if not confirm:
        errors["confirm_password"] = "Please confirm your password"
    elif password and confirm != password:
        errors["confirm_password"] = "Passwords do not match"

    return errors


def _validate_login(data):
    errors = {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not email:
        errors["email"] = "Email is required"
    elif "@" not in email:
        errors["email"] = "Enter a valid email address"
    if not password:
        errors["password"] = "Password is required"
    return errors


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json(silent=True) or {}
    errors = _validate_registration(data)
    if errors:
        return jsonify({"errors": errors}), 400

    password_hash = generate_password_hash(data["password"].strip())
    try:
        create_user(data["name"].strip(), data["email"].strip(), password_hash)
    except sqlite3.IntegrityError:
        return jsonify({"errors": {"email": "Email already registered"}}), 409
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({"error": "Internal server error"}), 500

    return jsonify({"success": True, "message": "Account created successfully"}), 201


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json(silent=True) or {}
    errors = _validate_login(data)
    if errors:
        return jsonify({"errors": errors}), 400

    user = get_user_by_email(data["email"].strip())
    if not user or not check_password_hash(user["password_hash"], data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    payload = {
        "sub": str(user["id"]),
        "name": user["name"],
        "email": user["email"],
        "iat": int(time.time()),
    }
    token = sign_jwt(payload, app.secret_key)
    return jsonify({
        "success": True,
        "data": {
            "token": token,
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        },
    }), 200


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/api/profile")
def api_profile():
    payload, err = _get_jwt_payload()
    if err:
        return jsonify({"error": err}), 401

    user_id = int(payload["sub"])
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    summary = get_expense_summary(user_id)
    member_since = (user["created_at"] or "")[:10]

    return jsonify({
        "success": True,
        "data": {
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "member_since": member_since,
            },
            "stats": {
                "total_expenses": summary["total_count"],
                "total_amount": summary["total_amount"],
                "by_category": summary["by_category"],
            },
        },
    }), 200


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
