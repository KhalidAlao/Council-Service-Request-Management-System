# Council Service Management System - REST API Specification


**Base URL:** `https://api.council.gov/api/v1`  
**Content-Type:** `application/json`

---

## 1. Authentication

All protected endpoints require a **Bearer Token** in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

- Access tokens expire after **15 minutes**.
- Refresh tokens expire after **7 days**.

---

## 2. Common Conventions

### Pagination

All list endpoints support:

- `page` (default: 1)
- `limit` (default: 20, max: 100)

**Example:** `GET /requests?page=2&limit=50`

### Date/Time Format

All timestamps are in ISO 8601 UTC: `YYYY-MM-DDTHH:mm:ssZ`

### Error Responses

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Status must be one of: UNDER_REVIEW, IN_PROGRESS",
    "details": { "field": "status" }
  }
}
```

| HTTP Status | Description |
|---|---|
| 200 | Success |
| 201 | Created |
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Rate limit exceeded |

---

## 3. Endpoints

### 3.1 Authentication

| Method | Path | Description | Allowed Roles |
|---|---|---|---|
| `POST` | `/auth/login` | Authenticate staff user, get tokens. | Guest |
| `POST` | `/auth/refresh` | Get new access token using refresh token. | Guest |

#### `POST /auth/login`

**Request:**

```json
{
  "email": "officer.jones@council.gov",
  "password": "securepassword123"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

---

### 3.2 Service Requests

| Method | Path | Description | Allowed Roles |
|---|---|---|---|
| `POST` | `/requests` | Submit a new request (guest or authenticated). | `Guest`, `Resident`, `Officer`, `Admin` |
| `GET` | `/requests/track` | Track by reference number. **Rate-limited** (10 req/min). | `Guest` |
| `GET` | `/requests` | List/filter with pagination. Residents see own only; staff see all. | `Resident`, `Officer`, `Admin` |
| `GET` | `/requests/{id}` | Get full details of a request. | `Resident` (own only), `Officer`, `Admin` |

#### `POST /requests`

**Request (authenticated user):**

```json
{
  "title": "Pothole on Main Street",
  "description": "Large pothole near the traffic lights.",
  "location": "Main Street, outside No. 45",
  "category": "ROADS",
  "priority": "HIGH"
}
```

**Request (guest – no Authorization header):**

```json
{
  "title": "Overflowing bin in park",
  "description": "The public bin near the playground is overflowing.",
  "location": "Central Park, near the swings",
  "category": "WASTE",
  "priority": "MEDIUM",
  "guest_name": "Jane Doe",
  "guest_email": "jane.doe@example.com",
  "guest_phone": "021 555 1234"
}
```

**Response (201):**

```json
{
  "request_id": 1001,
  "reference_number": "SR-2026-A7X92B",
  "status": "SUBMITTED",
  "date_submitted": "2026-08-08T10:30:00Z"
}
```

#### `GET /requests/track`

**Query:** `?reference=SR-2026-A7X92B`

**Response (200):**

```json
{
  "reference_number": "SR-2026-A7X92B",
  "status": "IN_PROGRESS",
  "title": "Pothole on Main Street",
  "location": "Main Street, outside No. 45",
  "date_submitted": "2026-08-08T10:30:00Z",
  "last_updated": "2026-08-08T14:15:00Z"
}
```

#### `GET /requests`

**Query Parameters:**

`status`, `priority`, `category`, `department_id`, `assigned_officer_id`, `date_from`, `date_to`, `page`, `limit`

**Example:** `GET /requests?status=UNDER_REVIEW&priority=HIGH&page=1&limit=20`

**Response (200):**

```json
{
  "data": [
    {
      "request_id": 1001,
      "reference_number": "SR-2026-A7X92B",
      "title": "Pothole on Main Street",
      "status": "UNDER_REVIEW",
      "priority": "HIGH",
      "category": "ROADS",
      "date_submitted": "2026-08-08T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 45,
    "total_pages": 3
  }
}
```

#### `GET /requests/{id}`

**Response (200):**

```json
{
  "request_id": 1001,
  "reference_number": "SR-2026-A7X92B",
  "title": "Pothole on Main Street",
  "description": "Large pothole near the traffic lights, approx 60cm wide.",
  "location": "Main Street, outside No. 45",
  "category": "ROADS",
  "priority": "HIGH",
  "status": "UNDER_REVIEW",
  "submitted_by": {
    "user_id": 42,
    "full_name": "John Resident",
    "email": "john@example.com"
  },
  "assigned_officer": {
    "user_id": 7,
    "full_name": "Officer Jones",
    "department": "Roads Maintenance"
  },
  "department": {
    "department_id": 1,
    "name": "Roads Maintenance"
  },
  "date_submitted": "2026-08-08T10:30:00Z",
  "last_updated": "2026-08-08T14:15:00Z"
}
```

---

### 3.3 Request Workflow (Status & Assignment)

| Method | Path | Description | Allowed Roles |
|---|---|---|---|
| `PATCH` | `/requests/{id}/status` | Update status. Officer → only `UNDER_REVIEW`/`IN_PROGRESS`. Admin → only `RESOLVED`/`CLOSED`. | `Officer`, `Admin` |
| `PATCH` | `/requests/{id}/assign` | Assign/reassign officer. Admin → any. Officer → self (if unassigned) or handoff (if current assignee). | `Officer` (restricted), `Admin` |

#### `PATCH /requests/{id}/status`

**Request:**

```json
{
  "status": "UNDER_REVIEW"
}
```

**Response (200):**

```json
{
  "request_id": 1001,
  "status": "UNDER_REVIEW",
  "last_updated": "2026-08-08T14:15:00Z"
}
```

#### `PATCH /requests/{id}/assign`

**Permission Rules:**

- **Admin:** Can assign any request to any officer.
- **Officer:** Can self-assign only if `assigned_officer_id` is `NULL`.
- **Officer:** Can reassign (handoff) only if they are the current assignee.
- **Officer:** Cannot assign an unassigned request to another officer.

**Request:**

```json
{
  "assigned_officer_id": 7
}
```

**Response (200):**

```json
{
  "request_id": 1001,
  "assigned_officer_id": 7,
  "assigned_officer_name": "Officer Jones",
  "last_updated": "2026-08-08T14:20:00Z"
}
```

**Error (403):**

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Officers can only self-assign unassigned requests, or hand off requests currently assigned to them."
  }
}
```

---

### 3.4 Internal Notes

| Method | Path | Description | Allowed Roles |
|---|---|---|---|
| `POST` | `/requests/{id}/notes` | Add an internal note. | `Officer` (assigned only), `Admin` |
| `GET` | `/requests/{id}/notes` | Fetch all notes. | `Officer` (assigned only), `Admin` |

#### `POST /requests/{id}/notes`

**Request:**

```json
{
  "body": "Roads department confirmed they can start resurfacing next Monday."
}
```

**Response (201):**

```json
{
  "note_id": 501,
  "request_id": 1001,
  "author": {
    "user_id": 7,
    "full_name": "Officer Jones"
  },
  "body": "Roads department confirmed they can start resurfacing next Monday.",
  "created_at": "2026-08-08T15:00:00Z"
}
```

#### `GET /requests/{id}/notes`

**Response (200):**

```json
{
  "data": [
    {
      "note_id": 500,
      "author": "Officer Jones",
      "body": "Request forwarded to Roads department for analysis.",
      "created_at": "2026-08-08T11:00:00Z"
    }
  ]
}
```

---

### 3.5 Audit History

| Method | Path | Description | Allowed Roles |
|---|---|---|---|
| `GET` | `/requests/{id}/audit` | Fetch immutable audit log. | `Officer` (assigned only), `Admin` |

#### `GET /requests/{id}/audit`

**Response (200):**

```json
{
  "data": [
    {
      "field_changed": "status",
      "old_value": "SUBMITTED",
      "new_value": "UNDER_REVIEW",
      "changed_by": "Officer Jones",
      "changed_at": "2026-08-08T14:15:00Z"
    },
    {
      "field_changed": "assigned_officer_id",
      "old_value": null,
      "new_value": "7",
      "changed_by": "Admin Smith",
      "changed_at": "2026-08-08T14:20:00Z"
    }
  ]
}
```

---

### 3.6 Admin: User Management

| Method | Path | Description | Allowed Roles |
|---|---|---|---|
| `GET` | `/admin/users` | List all users. Filter by `role` or `department_id`. | `Admin` |
| `POST` | `/admin/users` | Create a new staff user (Officer or Admin). | `Admin` |
| `PATCH` | `/admin/users/{id}/role` | Change a user's role. | `Admin` |
| `PATCH` | `/admin/users/{id}/department` | Assign/change an Officer's department. | `Admin` |
| `PATCH` | `/admin/users/{id}/deactivate` | Soft-delete (set `is_active = false`). | `Admin` |

#### `POST /admin/users`

**Request:**

```json
{
  "full_name": "Officer Jane Smith",
  "email": "jane.smith@council.gov",
  "phone": "021 555 6789",
  "password": "TemporaryPass123!",
  "role": "SUPPORT_OFFICER",
  "department_id": 3
}
```

**Response (201):**

```json
{
  "user_id": 101,
  "full_name": "Officer Jane Smith",
  "email": "jane.smith@council.gov",
  "role": "SUPPORT_OFFICER",
  "department_id": 3,
  "is_active": true,
  "created_at": "2026-08-08T16:00:00Z"
}
```

#### `PATCH /admin/users/{id}/deactivate`

**Request Body:** empty

**Response (200):**

```json
{
  "user_id": 101,
  "is_active": false,
  "deactivated_at": "2026-08-08T17:00:00Z"
}
```

---

## 4. Permission Matrix Summary

| Resource | Guest | Resident | Support Officer | Admin |
|---|---|---|---|---|
| `POST /auth/login` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/refresh` | ✅ | ✅ | ✅ | ✅ |
| `POST /requests` | ✅ | ✅ | ✅ | ✅ |
| `GET /requests/track` | ✅ (rate-limited) | ✅ | ✅ | ✅ |
| `GET /requests` | ❌ | ✅ (own only) | ✅ | ✅ |
| `GET /requests/{id}` | ❌ | ✅ (own only) | ✅ | ✅ |
| `PATCH /requests/{id}/status` (→ Review/Progress) | ❌ | ❌ | ✅ | ❌ |
| `PATCH /requests/{id}/status` (→ Resolved/Closed) | ❌ | ❌ | ❌ | ✅ |
| `PATCH /requests/{id}/assign` (self) | ❌ | ❌ | ✅ | ✅ |
| `PATCH /requests/{id}/assign` (other) | ❌ | ❌ | ❌ | ✅ |
| `POST/GET /requests/{id}/notes` | ❌ | ❌ | ✅ (assigned only) | ✅ |
| `GET /requests/{id}/audit` | ❌ | ❌ | ✅ (assigned only) | ✅ |
| `/admin/users/*` | ❌ | ❌ | ❌ | ✅ |
