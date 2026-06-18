# Spec: Login And Logout

## Overview
This step implements the login and logout flows — the gateway to the authenticated parts of Spendly. `POST /login` validates credentials, verifies the password hash, and issues a signed JWT token that the client stores in `localStorage`. All future protected routes will verify this token client-side (and eventually server-side). Logout is stateless by design: `GET /logout` redirects to `/`; a small JS snippet in `base.html` detects the navigation, clears `spendly_token` from `localStorage`, and completes the sign-out. This step also introduces the shared JWT helper module (`database/auth.py`) that registration and all future auth-protected routes will reuse.

## Routes

- `GET /login` — render the login form — public *(already exists as stub, no change needed to GET)*
- `POST /login` — accept JSON credentials, verify, return signed JWT — public
- `GET /logout` — clear client token via JS, redirect to `/` — public *(stub exists, needs implementation)*

---

## API Contract: POST /login

### Request

```
POST /login
Content-Type: application/json
```

#### Request body

| Field    | Type   | Required | Validation                           |
|---------|--------|----------|--------------------------------------|
| email   | string | yes      | non-empty, must contain `@`          |
| password| string | yes      | non-empty                            |

#### Example request

```json
{
  "email": "priya.sharma@example.com",
  "password": "secret123"
}
```

### Success response — `200 OK`

```json
{
  "success": true,
  "data": {
    "token": "<jwt_token_string>",
    "user": {
      "id": 3,
      "name": "Priya Sharma",
      "email": "priya.sharma@example.com"
    }
  }
}
```

### Validation error response — `400 Bad Request`

Returned when required fields are missing or malformed.

```json
{
  "errors": {
    "email": "Email is required",
    "password": "Password is required"
  }
}
```

### Authentication error response — `401 Unauthorized`

Returned for both "user not found" and "wrong password" — never reveal which one.

```json
{
  "error": "Invalid email or password"
}
```

### Unsupported content type — `415 Unsupported Media Type`

```json
{
  "error": "Content-Type must be application/json"
}
```

### Server error — `500 Internal Server Error`

```json
{
  "error": "Internal server error"
}
```

### Status codes

```
200 OK
400 Bad Request
401 Unauthorized
415 Unsupported Media Type
500 Internal Server Error
```

---

## Database changes

No new tables or columns. The `users` table already holds all required fields.

Add one new helper to `database/db.py`:
- `get_user_by_email(email)` — returns the matching `sqlite3.Row` or `None`. Parameterised query only.

## Templates

**Modify:**
- `templates/login.html` — remove `method="POST"` and `action` from the form; add a JS `fetch()` submit handler that posts JSON to `/POST /login`, stores the returned token in `localStorage`, and redirects to `/` on success; renders field-level and global errors on failure. Add client-side validation (both fields required, email must contain `@`) before the fetch fires.
- `templates/base.html` — add a small inline `<script>` in the `<head>` (or just before `</body>`) that checks `localStorage.getItem("spendly_token")`. When the user navigates to `GET /logout`, JS removes the token and redirects to `/`. No server-side session state is needed.

**Create:** none.

## Files to change

- `app.py` — add `check_password_hash` import from `werkzeug.security`; add `sign_jwt` import from `database.auth`; convert `GET /login` to `methods=["GET", "POST"]`; add POST handler; implement `GET /logout` redirect.
- `database/db.py` — add `get_user_by_email(email)` helper.
- `templates/login.html` — convert to JS fetch, client-side validation, token storage, inline errors.
- `templates/base.html` — add logout JS (token removal on `/logout` navigation).

## Files to create

- `database/auth.py` — JWT helper module with two functions:
  - `sign_jwt(payload: dict, secret: str) -> str` — wraps `jwt.encode(payload, secret, algorithm="HS256")` from PyJWT.
  - `decode_jwt(token: str, secret: str) -> dict` — wraps `jwt.decode(token, secret, algorithms=["HS256"])`; catches `jwt.InvalidTokenError` and re-raises as `ValueError`.

## New dependencies

- `PyJWT==2.13.0` — JWT signing and verification. Added to `requirements.txt`.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings or `.format()` in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All authentication uses JWT tokens — no Flask `session`, no `flash()`, no server-side cookies for auth state
- JWT payload must include: `sub` (user id as int), `name`, `email`, `iat` (issued-at unix timestamp as int)
- JWT signed with `app.secret_key` via HMAC-SHA256 using Python stdlib only
- `sign_jwt` and `decode_jwt` receive the secret as an explicit parameter — `database/auth.py` must not import from `app.py`
- Token stored client-side in `localStorage` under key `"spendly_token"`
- `POST /login` must check `Content-Type: application/json`; return `415` if missing
- Never distinguish "user not found" from "wrong password" in the error response — always return `401` with a generic message
- Logout is client-side only: JS removes `spendly_token` from `localStorage`; `GET /logout` on the server just redirects to `/`
- Follow all response envelope formats defined in `api-conventions.md`

## Definition of done

- [ ] `GET /login` renders the sign-in form
- [ ] `POST /login` with valid credentials returns `200` with a JWT token in `data.token` and user info in `data.user`
- [ ] After successful login, `localStorage.getItem("spendly_token")` returns a non-null JWT string in the browser console
- [ ] After successful login, the browser redirects to `/`
- [ ] `POST /login` with an unknown email returns `401` with `{"error": "Invalid email or password"}`
- [ ] `POST /login` with a wrong password returns `401` with the same generic message
- [ ] `POST /login` with missing email returns `400` with `errors.email` set
- [ ] `POST /login` with missing password returns `400` with `errors.password` set
- [ ] `POST /login` without `Content-Type: application/json` returns `415`
- [ ] Visiting `/logout` removes `spendly_token` from `localStorage` and redirects to `/`
- [ ] No Flask `session` or `flash` is used anywhere in this feature
- [ ] JWT token can be decoded and verified using `decode_jwt` in `database/auth.py`
- [ ] Client-side validation catches empty fields before the fetch fires
