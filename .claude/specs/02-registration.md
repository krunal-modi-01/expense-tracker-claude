# Spec: Registration

## Overview
This step implements user registration — the first point of entry for new Spendly users. It converts the existing `GET /register` stub into a fully functional sign-up flow. The form submits via JavaScript `fetch()` to `POST /register`, which validates input, hashes the password, inserts a new `users` row, and returns a success message. On success the client redirects to `/login`; validation and business errors are rendered inline without a page reload. No JWT token is issued here — token generation belongs to the login step, where the user explicitly authenticates with their credentials.

## Routes

- `GET /register` — render the registration form — public *(already exists as stub, no change needed)*
- `POST /register` — accept JSON body, validate, insert user, return success message — public

---

## API Contract: POST /register

### Request

```
POST /register
Content-Type: application/json
```

#### Request body

| Field            | Type   | Required | Validation                              |
|-----------------|--------|----------|-----------------------------------------|
| name            | string | yes      | non-empty, max 100 characters           |
| email           | string | yes      | must contain `@`, max 254 characters    |
| password        | string | yes      | min 6 characters, max 128 characters   |
| confirm_password| string | yes      | must match `password`                   |

#### Example request

```json
{
  "name": "Priya Sharma",
  "email": "priya.sharma@example.com",
  "password": "secret123",
  "confirm_password": "secret123"
}
```

### Success response — `201 Created`

```json
{
  "success": true,
  "message": "Account created successfully"
}
```

### Validation error response — `400 Bad Request`

Returned when any field fails format/length/match validation. All errors are returned in a single response.

```json
{
  "errors": {
    "name": "Name is required",
    "password": "Password must be at least 6 characters",
    "confirm_password": "Passwords do not match"
  }
}
```

### Business logic error response — `409 Conflict`

Returned when the email is already registered.

```json
{
  "errors": {
    "email": "Email already registered"
  }
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
201 Created
400 Bad Request
409 Conflict
415 Unsupported Media Type
500 Internal Server Error
```

---

## Database changes

No new tables or columns. The `users` table from Step 1 already has all required columns (`id`, `name`, `email`, `password_hash`, `created_at`).

Add one new helper to `database/db.py`:
- `create_user(name, email, password_hash)` — inserts a new user row, returns the new `id`. Parameterised query only.

## Templates

**Modify:**
- `templates/register.html` — remove native form `action`/`method` POST attributes; add a JS `fetch()` submit handler that posts JSON to `/register`, handles the JSON response (redirects to `/login` on success, renders field-level errors on failure).

**Create:** none.

## Files to change

- `app.py` — import `request`, `jsonify` from Flask; convert `GET /register` stub to `methods=["GET", "POST"]`; add POST handler with validation, `create_user()` call, JSON success response.
- `database/db.py` — add `create_user(name, email, password_hash)` helper.
- `templates/register.html` — wire up JS fetch submit, inline error rendering, client-side redirect to `/login` on success.

## Files to create

No new files.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings or `.format()` in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` before insert — never store plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No Flask `session`, no `flash()`, no server-side cookies for auth state
- No JWT token is issued at registration — token generation is deferred to the login step
- `POST /register` must check `Content-Type: application/json`; return `415` if missing
- `POST /register` must accept and return `application/json` — never return HTML from this endpoint
- Catch `sqlite3.IntegrityError` on duplicate email — return `409` JSON response, never let it 500
- Return all validation errors in a single response (do not short-circuit on first error)
- Never expose stack traces, SQL errors, or internal details in API responses
- Follow all response envelope formats defined in `api-conventions.md`

## Definition of done

- [ ] `GET /register` renders the sign-up form
- [ ] `POST /register` with valid JSON inserts a new `users` row with a hashed (not plaintext) password and returns `201` with `{"success": true, "message": "Account created successfully"}`
- [ ] After success, the browser redirects to `/login`
- [ ] No JWT token is present in the response or in `localStorage` after registration
- [ ] `POST /register` with a duplicate email returns `409` with `errors.email` set; no duplicate row is inserted
- [ ] `POST /register` with mismatched passwords returns `400` with `errors.confirm_password` set
- [ ] `POST /register` with a password shorter than 6 characters returns `400` with `errors.password` set
- [ ] `POST /register` with an empty name returns `400` with `errors.name` set
- [ ] All validation errors are returned together in one response (not one at a time)
- [ ] `POST /register` without `Content-Type: application/json` returns `415`
- [ ] No Flask `session` or `flash` is used anywhere in this feature
- [ ] The app starts without errors and `app.secret_key` is set
