# Council Service Management System - REST API Specification

**Document Version:** 1.1  
**Last Updated:** 2026-08-10  
**API Version:** v1  
**Base URL:** `https://api.council.gov/api/v1`  
**Content-Type:** `application/json`

---

## 1. Authentication

Protected endpoints require a Bearer access token:

```http
Authorization: Bearer <access_token>
```

- **Access token expiry:** 15 minutes
- **Refresh token expiry:** 7 days

---

## 2. Common Conventions

### 2.1 Pagination

| Parameter | Default | Maximum | Description |
|---|---:|---:|---|
| `page` | `1` | — | Page number |
| `limit` | `20` | `100` | Number of records returned |

Example:

```http
GET /requests?page=2&limit=50
```

### 2.2 Date/Time Format

All timestamps use ISO 8601 UTC:

```text
YYYY-MM-DDTHH:mm:ssZ
```

### 2.3 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Status must be one of: UNDER_REVIEW, IN_PROGRESS",
    "details": { "field": "status" }
  }
}
```

### 2.4 HTTP Status Codes

| Status | Description |
|---:|---|
| `200` | Request successful |
| `201` | Resource successfully created |
| `400` | Validation error / malformed request |
| `401` | Authentication required or invalid |
| `403` | Authenticated but insufficient permissions |
| `404` | Resource not found |
| `409` | Conflict |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

---

# 3. Authentication Endpoints

## 3.1 POST `/auth/login`

Authenticates a staff user and returns access and refresh tokens.

**Allowed role:** Guest

### Request

```json
{
  "email": "officer.jones@council.gov",
  "password": "securepassword123"
}
```

### Response `200`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "user_id": 7,
    "full_name": "Officer Jones",
    "email": "officer.jones@council.gov",
    "role": "SUPPORT_OFFICER",
    "department_id": 1
  }
}
```

> **Implementation enhancement:** The `user` object lets the frontend establish the authenticated user's identity, role and department without an additional request.

## 3.2 POST `/auth/refresh`

Returns a new access token using a valid refresh token.

**Allowed role:** Guest

### Request

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2..."
}
```

### Response `200`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

---

# 4. Service Request Endpoints

## 4.1 POST `/requests`

Creates a service request.

**Allowed roles:** Guest, Resident, Support Officer, Admin

### Authenticated User Request

```json
{
  "title": "Pothole on Main Street",
  "description": "Large pothole near the traffic lights.",
  "location": "Main Street, outside No. 45",
  "category": "ROADS",
  "priority": "HIGH"
}
```

### Guest User Request

Guests do not provide an authentication token.

```json
{
  "title": "Overflowing bin in park",
  "description": "The public bin near the playground is overflowing.",
  "location": "Central Park, near the swings",
  "category": "WASTE",
  "guest_name": "Jane Doe",
  "guest_email": "jane.doe@example.com",
  "guest_phone": "021 555 1234"
}
```

> **Priority:** If `priority` is omitted, it defaults to `MEDIUM`.

### Response `201`

```json
{
  "request_id": 1001,
  "reference_number": "SR-2026-A7X92B",
  "status": "SUBMITTED",
  "priority": "MEDIUM",
  "date_submitted": "2026-08-10T10:30:00Z"
}
```

## 4.2 GET `/requests/track`

Tracks a request using its reference number.

**Allowed role:** Guest

### Query Parameter

```http
GET /requests/track?reference=SR-2026-A7X92B
```

| Parameter | Required | Description |
|---|---|---|
| `reference` | Yes | Unique service request reference number |

### Response `200`

```json
{
  "reference_number": "SR-2026-A7X92B",
  "status": "IN_PROGRESS",
  "title": "Pothole on Main Street",
  "location": "Main Street, outside No. 45",
  "date_submitted": "2026-08-10T10:30:00Z",
  "last_updated": "2026-08-10T14:15:00Z"
}
```

> **Rate limiting:** This endpoint is limited to **10 requests per minute** per client.

## 4.3 GET `/requests`

Returns a paginated list of service requests.

**Allowed roles:** Resident, Support Officer, Admin

Residents see their own requests; staff see requests according to their permissions.

### Query Parameters

| Parameter | Description |
|---|---|
| `status` | Filter by request status |
| `priority` | Filter by priority |
| `category` | Filter by service category |
| `department_id` | Filter by department |
| `assigned_officer_id` | Filter by assigned officer |
| `date_from` | Return requests from this date |
| `date_to` | Return requests up to this date |
| `page` | Page number |
| `limit` | Number of results; maximum 100 |

### Example

```http
GET /requests?status=UNDER_REVIEW&priority=HIGH&category=ROADS&department_id=1&page=1&limit=20
```

### Response `200`

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
      "date_submitted": "2026-08-10T10:30:00Z"
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

## 4.4 GET `/requests/{id}`

Returns full request details.

**Allowed roles:** Resident (own only), Support Officer, Admin

### Response `200`

```json
{
  "request_id": 1001,
  "reference_number": "SR-2026-A7X92B",
  "title": "Pothole on Main Street",
  "description": "Large pothole near the traffic lights, approximately 60cm wide.",
  "location": "Main Street, outside No. 45",
  "category": "ROADS",
  "priority": "HIGH",
  "status": "UNDER_REVIEW",
  "rejection_reason": null,
  "duplicate_of_request_id": null,
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
  "date_submitted": "2026-08-10T10:30:00Z",
  "last_updated": "2026-08-10T14:15:00Z"
}
```

---

# 5. Request Workflow Endpoints

## 5.1 PATCH `/requests/{id}/status`

Updates a service request status.

**Allowed roles:** Support Officer, Admin

### Permission Rules

**Support Officer**
- May move requests to `UNDER_REVIEW`.
- May move requests to `IN_PROGRESS`.
- Cannot move requests to `RESOLVED` or `CLOSED`.

**Admin**
- May move requests to `RESOLVED`.
- May move requests to `CLOSED`.
- Cannot perform the Support Officer workflow transitions.

### Normal Transition Request

```json
{ "status": "UNDER_REVIEW" }
```

### DUPLICATE Request

```json
{
  "status": "DUPLICATE",
  "duplicate_of_request_id": 998
}
```

### REJECTED Request

```json
{
  "status": "REJECTED",
  "rejection_reason": "The reported issue is outside the council's jurisdiction."
}
```

### Valid Status Transitions

| Current Status | Valid Next Status | Role |
|---|---|---|
| `SUBMITTED` | `UNDER_REVIEW` | Support Officer |
| `UNDER_REVIEW` | `IN_PROGRESS` | Support Officer |
| `IN_PROGRESS` | `RESOLVED` | Admin |
| `RESOLVED` | `CLOSED` | Admin |
| `SUBMITTED` | `DUPLICATE` | Support Officer |
| `UNDER_REVIEW` | `DUPLICATE` | Support Officer |
| `SUBMITTED` | `REJECTED` | Support Officer |
| `UNDER_REVIEW` | `REJECTED` | Support Officer |

> **Terminal states:** `CLOSED`, `DUPLICATE` and `REJECTED` are terminal states. No further status transitions are permitted from these states.

### Response `200`

```json
{
  "request_id": 1001,
  "status": "UNDER_REVIEW",
  "duplicate_of_request_id": null,
  "rejection_reason": null,
  "last_updated": "2026-08-10T14:15:00Z"
}
```

## 5.2 PATCH `/requests/{id}/assign`

Assigns or reassigns a request.

**Allowed roles:** Support Officer (restricted), Admin

### Permission Rules

- **Admin:** Can assign any request to any officer.
- **Support Officer:** Can self-assign an unassigned request.
- **Support Officer:** Can hand off a request currently assigned to them.
- **Support Officer:** Cannot assign an unassigned request directly to another officer.

### Request

```json
{ "assigned_officer_id": 7 }
```

### Response `200`

```json
{
  "request_id": 1001,
  "assigned_officer_id": 7,
  "assigned_officer_name": "Officer Jones",
  "last_updated": "2026-08-10T14:20:00Z"
}
```

### Error `403`

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Officers can only self-assign unassigned requests, or hand off requests currently assigned to them."
  }
}
```

---

# 6. Internal Notes Endpoints

> **Read/write asymmetry:** `POST /notes` has stricter permissions because it modifies data. A Support Officer must be assigned to the request to create a note. `GET /notes` is more permissive within the staff workflow; authorised Support Officers can read permitted request notes, while Admins can access all notes.

## 6.1 POST `/requests/{id}/notes`

Adds an internal note.

**Allowed roles:** Support Officer (assigned only), Admin

### Request

```json
{ "body": "Roads department confirmed they can start resurfacing next Monday." }
```

### Response `201`

```json
{
  "note_id": 501,
  "request_id": 1001,
  "author": { "user_id": 7, "full_name": "Officer Jones" },
  "body": "Roads department confirmed they can start resurfacing next Monday.",
  "created_at": "2026-08-10T15:00:00Z"
}
```

## 6.2 GET `/requests/{id}/notes`

Returns internal notes.

**Allowed roles:** Support Officer, Admin

### Response `200`

```json
{
  "data": [
    {
      "note_id": 500,
      "author": "Officer Jones",
      "body": "Request forwarded to Roads department for analysis.",
      "created_at": "2026-08-10T11:00:00Z"
    }
  ]
}
```

---

# 7. Audit History Endpoint

## 7.1 GET `/requests/{id}/audit`

Returns the immutable audit history.

**Allowed roles:** Support Officer assigned to the request, Admin

### Response `200`

```json
{
  "data": [
    {
      "field_changed": "status",
      "old_value": "SUBMITTED",
      "new_value": "UNDER_REVIEW",
      "changed_by": "Officer Jones",
      "changed_at": "2026-08-10T14:15:00Z"
    },
    {
      "field_changed": "assigned_officer_id",
      "old_value": null,
      "new_value": "7",
      "changed_by": "Admin Smith",
      "changed_at": "2026-08-10T14:20:00Z"
    }
  ]
}
```

---

# 8. Admin User Management Endpoints

All endpoints in this section require the `Admin` role.

## 8.1 GET `/admin/users`

Lists staff users.

### Query Parameters

| Parameter | Description |
|---|---|
| `role` | Filter by role |
| `department_id` | Filter by department |
| `is_active` | Filter by active/inactive status |

## 8.2 POST `/admin/users`

Creates a staff user.

### Request

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

> `phone` is optional.

### Response `201`

```json
{
  "user_id": 101,
  "full_name": "Officer Jane Smith",
  "email": "jane.smith@council.gov",
  "phone": "021 555 6789",
  "role": "SUPPORT_OFFICER",
  "department_id": 3,
  "is_active": true,
  "created_at": "2026-08-10T16:00:00Z"
}
```

## 8.3 PATCH `/admin/users/{id}/role`

Changes a user's role.

### Request

```json
{ "role": "ADMIN" }
```

> **Conditional department clearing:** If the new role does not require a department assignment, the system may clear `department_id` automatically.

## 8.4 PATCH `/admin/users/{id}/department`

Assigns or changes an officer's department.

> **Role guard:** Department assignment is only valid for roles eligible for departmental membership, such as `SUPPORT_OFFICER`. The API must reject department assignment for roles that are not eligible.

### Request

```json
{ "department_id": 3 }
```

## 8.5 PATCH `/admin/users/{id}/deactivate`

Soft-deactivates a user.

### Request Body

Empty.

### Response `200`

```json
{
  "user_id": 101,
  "is_active": false,
  "deactivated_at": "2026-08-10T17:00:00Z"
}
```

---

# 9. Permission Matrix

| Endpoint | Guest | Resident | Support Officer | Admin |
|---|:---:|:---:|:---:|:---:|
| `POST /auth/login` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/refresh` | ✅ | ✅ | ✅ | ✅ |
| `POST /requests` | ✅ | ✅ | ✅ | ✅ |
| `GET /requests/track` | ✅ | ✅ | ✅ | ✅ |
| `GET /requests` | ❌ | ✅ Own | ✅ | ✅ |
| `GET /requests/{id}` | ❌ | ✅ Own | ✅ | ✅ |
| `PATCH /requests/{id}/status` → `UNDER_REVIEW` | ❌ | ❌ | ✅ | ❌ |
| `PATCH /requests/{id}/status` → `IN_PROGRESS` | ❌ | ❌ | ✅ | ❌ |
| `PATCH /requests/{id}/status` → `RESOLVED` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /requests/{id}/status` → `CLOSED` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /requests/{id}/status` → `DUPLICATE` | ❌ | ❌ | ✅ | ❌ |
| `PATCH /requests/{id}/status` → `REJECTED` | ❌ | ❌ | ✅ | ❌ |
| `PATCH /requests/{id}/assign` — self | ❌ | ❌ | ✅ | ✅ |
| `PATCH /requests/{id}/assign` — other | ❌ | ❌ | ❌ | ✅ |
| `POST /requests/{id}/notes` | ❌ | ❌ | ✅ Assigned | ✅ |
| `GET /requests/{id}/notes` | ❌ | ❌ | ✅ Permitted | ✅ |
| `GET /requests/{id}/audit` | ❌ | ❌ | ✅ Assigned | ✅ |
| `GET /admin/users` | ❌ | ❌ | ❌ | ✅ |
| `POST /admin/users` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /admin/users/{id}/role` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /admin/users/{id}/department` | ❌ | ❌ | ❌ | ✅ |
| `PATCH /admin/users/{id}/deactivate` | ❌ | ❌ | ❌ | ✅ |

---

# 10. Rate Limiting

| Endpoint Group | Limit |
|---|---:|
| `GET /requests/track` | **10 requests/minute** |
| All other endpoints | **100 requests/minute** |

Rate limits are applied per client/IP according to the API gateway configuration.

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 97
X-RateLimit-Reset: 1723291200
```

When a limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

---

# 11. Versioning

All endpoints use the `/api/v1/` prefix.

Example:

```text
https://api.council.gov/api/v1/requests
```

### Breaking Changes Policy

Breaking changes require a new API major version. Examples include removing an endpoint, removing or renaming a required field, changing authentication requirements, or making an incompatible response-structure change.

### Deprecation Policy

Deprecated endpoints or API versions receive at least **6 months' notice** before removal.

---

# 12. Documentation Metadata

| Field | Value |
|---|---|
| Document | Council Service Management System REST API Specification |
| Document Version | `1.1` |
| API Version | `v1` |
| Last Updated | `2026-08-10` |
| Base URL | `https://api.council.gov/api/v1` |
| Format | REST / JSON |
