# Council Service Management System — Implementation Status Summary

**Status as of:** August 2026

---

## 1. Overview

This document summarizes the current implementation status of the Council Service Management System. The backend REST API (16 endpoints across 6 resource areas), an automated test suite, a curl/bash smoke-test script, and a full working frontend are all complete. This document records conscious design decisions, resolved bugs, and explicitly scoped-out features to provide clarity on the project's boundaries.

---

## 2. Implemented Endpoints

### 2.1 Authentication (/api/v1/auth/*)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| /auth/login | POST | Done | Authenticate user, return JWT tokens (access + refresh) |
| /auth/refresh | POST | Done | Refresh access token using refresh token |

### 2.2 Service Requests (/api/v1/requests)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| /requests | POST | Done | Submit new request (guest or authenticated) |
| /requests/track | GET | Done | Public tracking by reference number, no auth required, trimmed PII-free response |
| /requests | GET | Done | List/filter requests with pagination and role-based scoping |
| /requests/{id} | GET | Done | Get single request details with ownership checks |

### 2.3 Request Workflow (/api/v1/requests/{id}/*)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| /status | PATCH | Done | Update status with state machine + role-based transitions, DUPLICATE/REJECTED side-states |
| /assign | PATCH | Done | Assign/reassign officer with full permission matrix |

### 2.4 Internal Notes (/api/v1/requests/{id}/notes)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| /notes | POST | Done | Add internal note (assigned officer or admin; any officer if unassigned) |
| /notes | GET | Done | View all notes on a request (any officer/admin) |

### 2.5 Audit History (/api/v1/requests/{id}/audit)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| /audit | GET | Done | Retrieve chronological audit log (admin any; officer if assigned or request unassigned) |

### 2.6 Admin User Management (/api/v1/admin/*)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| /admin/users | GET | Done | List all users with filters and pagination |
| /admin/users | POST | Done | Create staff user (Officer or Admin) |
| /admin/users/{id}/role | PATCH | Done | Update user role with conditional department logic |
| /admin/users/{id}/department | PATCH | Done | Update officer's department (role guard) |
| /admin/users/{id}/deactivate | PATCH | Done | Soft-deactivate user with self-protection |
| /admin/departments | GET | Done | List departments (added during frontend work, for the admin UI dropdown) |

---

## 3. Endpoint Summary

| Category | Complete | Total |
|----------|----------|-------|
| Authentication | 2 | 2 |
| Service Requests | 4 | 4 |
| Workflow | 2 | 2 |
| Internal Notes | 2 | 2 |
| Audit History | 1 | 1 |
| Admin Users/Departments | 6 | 6 |
| **Total** | **17** | **17** |

**All 16 originally-planned endpoints are complete, plus one added during frontend development (`GET /admin/departments`).**

---

## 4. Automated Test Suite

Manual `curl`-based testing (used throughout backend development) was superseded by an automated pytest suite for repeatability and regression safety, after several rounds of manual test-account contamination made the case for isolated fixtures directly.

| Layer | File(s) | Count |
|-------|---------|-------|
| Unit | `test_status_transitions.py`, `test_assignment_rules.py` | 16 |
| Integration | `test_requests.py`, `test_status.py`, `test_assign.py`, `test_notes.py`, `test_audit.py`, `test_admin_users.py`, `test_auth_flow.py` | 87 |
| **Total** | | **103** |

**Test database:** isolated in-memory SQLite per test function (`scope='function'`), preventing the cross-test contamination encountered during manual testing.

**Coverage:** 90% (776 statements, 75 missed).

### 4.1 Curl/Bash Smoke Test

`scripts/smoke_test.sh` — a standalone, rerunnable end-to-end test script covering the full happy-path workflow (admin login → dynamic staff creation → guest submission → self-assignment → full status state machine → notes → audit log) plus negative/permission checks, with colored pass/fail output and a final tally. Built using bash functions, safe array-based `curl` invocation (not string-concatenated `eval`), and `jq -n` for safe JSON construction.

### 4.2 Tested Permission Scenarios

| Role | GET /requests | GET /requests/{id} | PATCH /status | PATCH /assign | POST /notes | GET /notes | GET /audit |
|------|---------------|---------------------|----------------|----------------|--------------|-------------|------------|
| Guest | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| Resident | Own only | Own only | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| Officer | All | All | Review/Progress | Self/Handoff | Assigned only (any if unassigned) | All | Assigned only (any if unassigned) |
| Admin | All | All | Resolved/Closed | Any | All | All | All |

---

## 5. Frontend

A vanilla JavaScript single-page application, no framework or build step, served by Flask as static files from the same origin (avoiding CORS entirely).

| Page | Status | Notes |
|------|--------|-------|
| Login | Done | Email/password, stores JWT + role + user ID in `localStorage` |
| Submit | Done | Guest and authenticated submission, conditional guest-field display |
| Track | Done | Public reference-number lookup, PII-free response |
| Dashboard | Done | List/filter (status, category, priority), pagination |
| Request Detail | Done | Full detail view, role-gated status transitions (with conditional `DUPLICATE`/`REJECTED` fields), assignment, notes, audit log |
| Admin Users | Done | List, create staff accounts, deactivate |

**Routing:** hash-based (`#/path`), with a hand-written router supporting both exact routes and `:param`-style path parameters (e.g., `/detail/:id`), and a route guard blocking protected paths when no token is present.

**Not exposed in the UI (supported by the API, not built into a form):** role change and department change for existing users — `PATCH /admin/users/{id}/role` and `/department` exist and are tested, but the admin page only exposes create + deactivate given time constraints.

---

## 6. Conscious Deviations from Original Spec

| Area | Specification | Implementation | Rationale |
|------|----------------|------------------|-----------|
| priority field | Client-supplied | System defaults to MEDIUM | Prevents residents from marking everything as URGENT; preserves officer triage integrity |
| password_hash | Null for guests | NOT NULL | Guests don't get user rows in this design |
| Notes GET | Officer (assigned only) | Any officer/admin can read | Supports situational awareness and collaboration; read-only, low risk |
| Audit GET | Admin only | Admin, plus assigned officer / any officer on unassigned requests | Assigned officers need context on their own requests' history |
| Status DUPLICATE/REJECTED | Not in original spec | Implemented, with `rejection_reason` and `duplicate_of_request_id` | Matches ERD requirements from Phase 1 design |
| Login response user data | Not specified | Included | Richer response provides frontend with user details |
| Track endpoint response | Not detailed | Trimmed public schema (no submitter PII, no assigned officer, no department) | Prevents data exposure via guessed/known reference numbers |

---

## 7. Resolved Bugs

A running record of real bugs found and fixed during development — kept visible rather than removed, as evidence of an application-support mindset (find, diagnose, fix, verify) rather than presenting the project as built perfectly the first time.

| Bug | Found During | Resolution |
|-----|---------------|-----------|
| `rejection_reason` validated but never persisted | Post-Phase-4 documentation review | Added missing column + migration, fixed route to persist the value, verified via direct DB query |
| `submitted_by` schema field silently empty | Manual testing of authenticated submission | Marshmallow field name (`submitted_by`) didn't match the model relationship's actual attribute (`submitter`) — fixed with `attribute='submitter'` |
| `Query.get()` deprecation warnings across the codebase | Full pytest run after test suite completion | Project-wide refactor to `Session.get()`, re-verified all 103 tests still passed |
| Seed script mutated by manual admin-endpoint testing, contaminating "known" test accounts | Notes-endpoint permission testing | Diagnosed via `GET /admin/users/{id}`, repaired accounts through the admin API itself (doubling as a real test), then adopted a stricter fresh-account-per-test-round discipline |
| Smoke test: `api_call` set "global" status/body variables from inside a `$(...)` subshell, which never propagated to the caller | Building the curl smoke-test script | Restructured `api_call` to return a single delimited string on stdout; caller (`do_call`) splits it in the real shell, not a subshell |
| Smoke test: missing `-H` flag on the `Authorization` header argument | Same debugging session | Header string was appended to curl's argument array without its required `-H` flag |
| Frontend: `<script>` tag injected via `innerHTML` never executed (status-field toggle) | Building the request detail page | Browsers do not execute injected `<script>` tags; moved the toggle logic to a real `addEventListener` call after the DOM was in place |
| Frontend: `router.js` served as an empty (0-byte) file despite editor showing content | Building path-parameter routing | Confirmed via the raw HTTP response (`Content-Length: 0`), not the editor; recreated the file directly via terminal |

---

## 8. Explicitly Out of Scope (Conscious Limitations)

| Feature | Reason | Decision Reference |
|---------|--------|----------------------|
| Admin action audit logging | `audit_log` table is scoped to service requests (non-nullable `request_id` FK) | Phase 4 decision |
| Deactivation side-effects | Auto-reassignment of a deactivated officer's requests is complex (who to reassign to?) | Phase 4 decision |
| Admin self-protection for department changes | Changing your own department doesn't lock you out of anything | Phase 4 decision |
| Resident self-registration | Residents interact primarily as guests | Phase 1 decision |
| Guest password hashing | Guests don't get `users` rows at all | Phase 3 decision |
| Invite/password reset flow | Adds significant complexity beyond project scope | Phase 4 decision |
| Rate-limiting on /requests/track | Flask-Limiter not installed; reference number entropy (36^8 ≈ 2.8 trillion combinations) mitigates brute-force risk at this scale | Phase 4 decision |
| Role/department change UI (admin page) | API fully supports and tests these; frontend only exposes create + deactivate given time constraints | Phase 5 decision |
| URL-synced dashboard filter state | Kept filters as in-memory DOM state rather than URL query params, for simplicity | Phase 5 decision |

---

**Document version:** 3.0.0
**Last updated:** 2026-08-11
**Status:** Backend (17/17 endpoints), automated testing (103 tests, 90% coverage, smoke script), and frontend (6/6 pages) all complete.