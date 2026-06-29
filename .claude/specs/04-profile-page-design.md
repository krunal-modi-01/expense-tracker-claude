# Spec: Profile Page Design

## Overview

The profile page is the first authenticated view in Spendly. It gives a logged-in user a personal summary: their account details (name, email, member since) and a snapshot of their spending activity (total expenses logged, total amount spent, and a per-category breakdown). Because the app uses stateless JWT authentication stored in `localStorage`, the page is rendered as a shell by the server and the JS layer enforces auth — if no token is present, the user is redirected to `/login`. Data is loaded from a protected JSON endpoint (`GET /api/profile`) that validates the `Authorization: Bearer <token>` header.

---

## Routes

- `GET /profile` — renders `profile.html` shell; no server-side auth check (JS handles redirect) — public route, auth enforced client-side
- `GET /api/profile` — returns JSON with user info and expense summary; requires valid JWT in `Authorization` header — private

---

## Database changes

No new tables or columns. Two new query helpers are needed in `database/db.py`:

- `get_user_by_id(user_id)` — `SELECT * FROM users WHERE id = ?`
- `get_expense_summary(user_id)` — returns `total_count`, `total_amount`, and per-category totals using:
  ```sql
  SELECT category, COUNT(*) as count, SUM(amount) as total
  FROM expense
  WHERE user_id = ?
  GROUP BY category
  ORDER BY total DESC
  ```

---

## Templates

**Create:**
- `templates/profile.html` — extends `base.html`; shows a loading state until JS fetches data; renders name, email, member-since date, and expense stats once loaded

**Modify:**
- `templates/base.html` — update the auth-aware navbar: when a JWT token is present replace "Sign in / Get started" with a "Profile" link (`/profile`) and a "Sign out" link instead of just "Sign out" alone

---

## Files to change

- `app.py` — add `GET /api/profile` route and replace the `/profile` stub with a proper `render_template` call; import `get_user_by_id`, `get_expense_summary` from `database.db`; import `decode_jwt` from `database.auth`
- `database/db.py` — add `get_user_by_id` and `get_expense_summary`
- `templates/base.html` — update navbar JS to include Profile link when authenticated
- `static/css/style.css` — add profile page layout and stats card styles using existing CSS variables

---

## Files to create

- `templates/profile.html`
- `tests/test_profile.py`

---

## New dependencies

No new dependencies.

---

## API Contract

### `GET /api/profile`

**Request:**
```http
GET /api/profile HTTP/1.1
Authorization: Bearer <jwt_token>
```

**Success response — 200 OK:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "name": "Nitish Kumar",
      "email": "nitish@example.com",
      "member_since": "2026-05-01"
    },
    "stats": {
      "total_expenses": 12,
      "total_amount": 4820.50,
      "by_category": [
        { "category": "Food", "count": 5, "total": 1200.00 },
        { "category": "Transport", "count": 3, "total": 540.00 }
      ]
    }
  }
}
```

**Auth error — 401 Unauthorized (missing or invalid token):**
```json
{
  "error": "Authentication required"
}
```

```json
{
  "error": "Invalid or expired token"
}
```

**Status codes:**

```
200 OK
401 Unauthorized
500 Internal Server Error
```

---

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — no f-strings or `.format()` in SQL
- Passwords hashed with werkzeug (no changes needed here)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All authentication/authorization must use JWT token — no cookie or session-based auth on server side
- JWT extracted from `Authorization: Bearer <token>` header on the API route
- If the header is missing or malformed → 401 `{"error": "Authentication required"}`
- If the token fails `decode_jwt` → 401 `{"error": "Invalid or expired token"}`
- `GET /profile` (the page route) must **not** do a server-side auth check — it renders the shell and lets JS redirect unauthenticated users
- Follow `api-conventions.md` for all JSON response shapes
- `member_since` must be formatted as `YYYY-MM-DD` (slice from `created_at` stored in DB)

---

## Definition of done

- [ ] `GET /profile` returns 200 and renders the profile page HTML
- [ ] Visiting `/profile` without a token in `localStorage` redirects to `/login` (verified in browser)
- [ ] Visiting `/profile` with a valid token shows the user's name, email, and member-since date
- [ ] Expense stats (total count, total amount, by-category breakdown) render correctly
- [ ] `GET /api/profile` with a valid `Authorization: Bearer <token>` header returns 200 with correct JSON shape
- [ ] `GET /api/profile` with no `Authorization` header returns 401 `{"error": "Authentication required"}`
- [ ] `GET /api/profile` with a tampered token returns 401 `{"error": "Invalid or expired token"}`
- [ ] Navbar shows "Profile" and "Sign out" links when a token is in `localStorage`
- [ ] Navbar reverts to "Sign in / Get started" after signing out
- [ ] `pytest tests/test_profile.py` passes all tests
- [ ] `pytest tests/` passes with no regressions in registration or login tests
