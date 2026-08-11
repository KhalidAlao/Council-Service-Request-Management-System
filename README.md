# Council Service Request Management System

A full-stack web application for managing council service requests — residents can report issues (potholes, waste collection problems, streetlight faults, etc.), and council staff triage, assign, and resolve them through a role-based workflow with a complete audit trail.

Built as a portfolio project demonstrating REST API design, relational database design, role-based access control, automated testing, and full-stack development.

**Repository:** https://github.com/KhalidAlao/Council-Service-Request-Management-System

## Features

- **Public request submission** — residents can report issues as a guest or while signed in, with automatic reference number generation and department routing based on category
- **Public tracking** — anyone can check a request's status by reference number, with no personal data exposed
- **Role-based staff workflow** — a forward-only status state machine (`Submitted → Under Review → In Progress → Resolved → Closed`, plus `Duplicate`/`Rejected` side-states) with different permissions for support officers and admins
- **Assignment rules** — officers can self-assign unassigned requests or hand off their own; only admins can assign to any officer
- **Internal notes** — private staff-only collaboration notes attached to each request
- **Full audit trail** — every status change and assignment is logged with who, what, when, old value, and new value
- **Admin user management** — create staff accounts, change roles/departments, deactivate users
- **JWT authentication** with role claims embedded in the token
- **103 automated tests** (pytest, unit + integration, ~90% coverage) plus a bash/curl smoke-test script

## Screenshots

![Request Detail](<Screenshot 2026-08-12 at 00.05.28.png>)
![Request Dashboard](<Screenshot 2026-08-12 at 00.08.10.png>)
![Admin Page](<Screenshot 2026-08-12 at 00.09.37.png>)



## Tech Stack

**Backend:** Flask, SQLAlchemy, Flask-Migrate (Alembic), Flask-JWT-Extended, Marshmallow, pytest
**Database:** SQLite (development), designed for PostgreSQL compatibility
**Frontend:** Vanilla JavaScript (ES modules), hash-based client-side routing, no framework or build step
**Testing:** pytest (unit + integration), bash/curl smoke test script
**CI:** GitHub Actions (lint with flake8, test with pytest)

## Architecture

- **Single `users` table** with a `roles` lookup table, rather than one table per role — keeps authentication and permission checks in one place
- **Guests never touch the `users` table** — contact info is stored directly on the request, keeping the guest-submission path simple and avoiding fragile account-matching logic
- **Six-table schema:** `roles`, `departments`, `users`, `service_requests`, `request_notes`, `audit_log`
- **Forward-only status state machine**, enforced server-side, with explicit permission gates per role (officers can only move a request to `Under Review`/`In Progress`; only admins can `Resolve`/`Close`)
- **`department_id` auto-derived from `category`** at submission time via a fixed mapping, rather than left to the submitter to choose

Full design documentation, including user stories, ER diagram, and API specification, is in [`docs/`](./docs).

## Getting Started

### Prerequisites
- Python 3.9+
- `pip` and `venv`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then fill in JWT_SECRET_KEY, etc.

flask db upgrade                # apply migrations
python scripts/seed_data.py     # seed roles, departments, and a default admin user

flask run
```

The app (backend API **and** frontend) will be available at `http://127.0.0.1:5000` — Flask serves the frontend's static files directly, so there's nothing separate to start.

Default admin login after seeding: `admin@council.gov` / `admin123` (override via `ADMIN_EMAIL`/`ADMIN_PASSWORD` environment variables).

### Running Tests

```bash
cd backend
pytest tests/                          # full test suite
pytest --cov=app tests/                # with coverage report
./scripts/smoke_test.sh                # end-to-end curl smoke test (requires a running server)
```

## API Overview

All endpoints are versioned under `/api/v1/`. Full specification in [`docs/api-spec.md`](./docs/api-spec.md).

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/login`, `POST /auth/refresh` |
| Requests | `POST /requests`, `GET /requests`, `GET /requests/{id}`, `GET /requests/track` |
| Workflow | `PATCH /requests/{id}/status`, `PATCH /requests/{id}/assign` |
| Notes | `POST/GET /requests/{id}/notes` |
| Audit | `GET /requests/{id}/audit` |
| Admin | `GET/POST /admin/users`, `PATCH /admin/users/{id}/role`, `PATCH /admin/users/{id}/department`, `PATCH /admin/users/{id}/deactivate`, `GET /admin/departments` |

## Role Permissions Summary

| Action | Resident | Support Officer | Admin |
|--------|----------|------------------|-------|
| Submit a request | ✅ (own) | ✅ | ✅ |
| View requests | Own only | All | All |
| Move to Under Review / In Progress | ❌ | ✅ | ❌ |
| Move to Resolved / Closed | ❌ | ❌ | ✅ |
| Self-assign / hand off | ❌ | ✅ (rules apply) | — |
| Assign any officer | ❌ | ❌ | ✅ |
| Add / view internal notes | ❌ | ✅ (assigned, or unassigned requests) | ✅ |
| View audit log | ❌ | ✅ (assigned, or unassigned requests) | ✅ |
| Manage staff users | ❌ | ❌ | ✅ |

## Documentation

- [`docs/user-stories.md`](./docs/user-stories.md) — user stories and acceptance criteria
- [`docs/er-diagram.md`](./docs/er-diagram.md) — entity-relationship diagram and schema rationale
- [`docs/api-spec.md`](./docs/api-spec.md) — full REST API specification
- [`docs/implementation-status.md`](./docs/implementation-status.md) — current implementation status, test coverage, and conscious scope decisions

## What This Project Demonstrates

- **Systems & database design** — user stories → ER diagram → REST API spec, all designed before implementation, with documented rationale for schema decisions
- **Python / SQL** — Flask REST API, SQLAlchemy ORM, Alembic migrations, hand-written and reviewed SQL schema
- **Curl / shell scripting** — a full bash smoke-test script with reusable functions, safe argument handling (arrays over string concatenation), JSON construction via `jq`, and colored pass/fail assertions
- **JavaScript / HTML5 / CSS3** — a working vanilla JS single-page frontend with no framework, covering the full user and staff workflow
- **Application support mindset** — a documented history of real bugs found and fixed (see [`docs/implementation-status.md`](./docs/implementation-status.md)) 

## License
MIT