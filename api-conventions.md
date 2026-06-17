# API Specification Standards

## Purpose

All API endpoints must have a fully defined contract before implementation begins. Specifications must clearly document request formats, response formats, validation rules, and error handling to ensure consistency across the application.

---

## Mandatory API Contract Definition

Every API specification must include:

* HTTP method
* Route path
* Authentication requirements
* Required headers
* Request body schema
* Validation rules
* Success response schema
* Error response schema
* HTTP status codes
* Example requests
* Example responses

An API specification is considered incomplete if request and response formats are not documented.

---

## Request Standards

### Request Format

Every endpoint must explicitly define:

* HTTP method
* URL path
* Required headers
* Request body fields
* Field types
* Required vs optional fields
* Validation requirements

### JSON APIs

All JSON endpoints must use:

```http
Content-Type: application/json
```

### Example Request

```json
{
  "email": "john@example.com",
  "password": "secret123"
}
```

### Validation Rules

Each field must define:

* Data type
* Required/optional status
* Minimum length
* Maximum length
* Allowed values
* Format requirements

Example:

```text
email:
- required
- string
- max length 254
- must contain '@'

password:
- required
- string
- minimum length 6
- maximum length 128
```

---

## Response Standards

### General Rules

* All API responses must return JSON.
* All success and error responses must be documented.
* Every response must specify its HTTP status code.
* Never expose stack traces or internal implementation details.

---

## Success Response Format

For data responses:

```json
{
  "success": true,
  "data": {}
}
```

For action-based responses:

```json
{
  "success": true,
  "message": "Operation completed successfully"
}
```

### Example

```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "john@example.com"
  }
}
```

Status:

```text
200 OK
```

or

```text
201 Created
```

---

## Validation Error Format

All validation errors must be returned in a single response.

Example:

```json
{
  "errors": {
    "email": "Invalid email address",
    "password": "Password must be at least 6 characters"
  }
}
```

Status:

```text
400 Bad Request
```

---

## Business Logic Error Format

Business rule violations should return field-specific errors.

Example:

```json
{
  "errors": {
    "email": "Email already registered"
  }
}
```

Status:

```text
409 Conflict
```

Other examples:

```json
{
  "errors": {
    "budget": "Monthly budget exceeded"
  }
}
```

---

## Authentication Error Format

Example:

```json
{
  "error": "Authentication required"
}
```

Status:

```text
401 Unauthorized
```

Example:

```json
{
  "error": "Invalid or expired token"
}
```

Status:

```text
401 Unauthorized
```

---

## Authorization Error Format

Example:

```json
{
  "error": "Permission denied"
}
```

Status:

```text
403 Forbidden
```

---

## Resource Not Found Format

Example:

```json
{
  "error": "Resource not found"
}
```

Status:

```text
404 Not Found
```

---

## Unsupported Content Type Format

Example:

```json
{
  "error": "Content-Type must be application/json"
}
```

Status:

```text
415 Unsupported Media Type
```

---

## Generic Error Format

Unexpected server failures must never expose internal details.

Example:

```json
{
  "error": "Internal server error"
}
```

Status:

```text
500 Internal Server Error
```

---

## Documentation Requirements

Every endpoint specification must include:

### Example Request

```json
{
  "email": "john@example.com",
  "password": "secret123"
}
```

### Example Success Response

```json
{
  "success": true,
  "message": "Login successful"
}
```

### Example Validation Error Response

```json
{
  "errors": {
    "email": "Invalid email address"
  }
}
```

### Example Business Error Response

```json
{
  "errors": {
    "email": "Email already registered"
  }
}
```

### Status Codes

All possible status codes must be documented.

Example:

```text
200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
415 Unsupported Media Type
500 Internal Server Error
```

---

## Implementation Rules

* Use consistent request and response structures across all endpoints.
* Return all validation errors in a single response whenever possible.
* Never return HTML from API endpoints.
* Never expose stack traces, SQL errors, or framework internals.
* All API specifications must include request and response examples before implementation begins.
* New endpoints must follow these standards unless an explicit exception is documented in the specification.
