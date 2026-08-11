# User Stories

User stories for the Council Service Request Management System, organized by role. Each role's stories were drafted first, then refined through several rounds of clarifying ambiguous behavior before any schema or API design began.

---

## Resident

- As a resident, I want to submit an issue whether or not I have an account, so that I can report a problem without friction.
- As a signed-in resident, I want to view my past requests and track their status, so that I know what's happening with something I reported.
- As a resident, I want every request I submit to have a title, description, category, and location, so that the council has enough information to act on it.
- As an unauthenticated (guest) resident, I want to provide my name, email, and phone number when submitting, so that the council can contact me and I can track the request later.
- As a resident, I want a platform to report issues, request services, and make general inquiries, so that I have one place to interact with the council.
- As a guest, I want to be given a unique reference number when I submit a request, so that I can track it later without needing an account.

**Acceptance criteria (submission form validation):**
- Given I am a resident on the submission form
- When I submit without filling in the title or description field
- Then I should see a validation error and the form should not submit

**Design decisions arising from this role:**
- Guests never get a row in the `users` table — their contact details are stored directly on the request (`guest_name`, `guest_email`, `guest_phone`), keeping tracking-by-reference simple and avoiding fragile guest-account matching.
- `priority` is never resident-supplied — it defaults to `MEDIUM` server-side, so triage integrity isn't undermined by residents marking everything urgent.

---

## Support Officer

- As a support officer, I want to manage requests and pass valid ones through the correct workflow, so that issues are properly triaged before being resolved.
- As a support officer, I want to see all requests but only act on the ones assigned to me, so that work is clearly owned and accountable.
- As a support officer, I want to move a request from `Submitted` to `Under Review`, so that I can begin triaging it.
- As a support officer, I want to identify duplicate requests and link them to the original, so that the council doesn't do the same work twice.
- As a support officer, I want to reject a request that isn't valid or within the council's jurisdiction, with a documented reason, so that there's a record of why it wasn't actioned.
- As a support officer, I want to assign priority levels to issues during triage, so that more urgent problems are visible.
- As a support officer, I want to self-assign an unassigned request or hand off one already assigned to me, so that ownership can move between officers when needed.

**Acceptance criteria (status transition + escalation workflow):**

- Given a service request exists with the status "Submitted"
- And a Support Officer is logged in
- When the Support Officer moves the request to "Under Review"
- Then the Support Officer notifies the relevant department to analyze the request
- When the department confirms the work is feasible
- Then the system alerts the Support Officer
- And the Support Officer moves the request to "In Progress"
- But only Admins are permitted to subsequently move the request to "Resolved" or "Closed"

**Design decisions arising from this role:**
- Officers may only set status to `Under Review`, `In Progress`, `Duplicate`, or `Rejected` — never `Resolved`/`Closed`.
- `Duplicate` and `Rejected` are reachable only from `Submitted` or `Under Review` — once work has started (`In Progress` or later), a request can no longer be marked as one of these; it's too late for either judgement to apply.
- Assignment rules: an officer may self-assign only if a request is currently unassigned, or hand off a request currently assigned to them. They cannot assign an unassigned request to someone else, or reassign a request that isn't theirs.
- The "officer messages the relevant department" step is logged as an internal note on the request, not a separate department-messaging feature — kept in scope as a lightweight text log rather than building real inter-department messaging.

---

## Admin

- As an admin, I want to see all requests, including ones not yet triaged by an officer, so that I have full visibility of the system.
- As an admin, I want to be the one who finalizes requests — moving them to `Resolved` or `Closed` — so that closing a request is a deliberate, accountable action separate from day-to-day triage.
- As an admin, I want to communicate with the relevant council services to resolve requests, so that the actual work gets done (this communication happens outside the system; only the outcome is reflected in status changes).
- As an admin, I want to manage users and roles — creating staff accounts, changing roles, assigning officers to departments, and deactivating accounts — so that I control who has access to the system and what they can do.
- As an admin, I want to prevent myself from deactivating or changing my own role, so that I can't accidentally lock myself out of the system.

**Design decisions arising from this role:**
- Admins may only set status to `Resolved` or `Closed` — the reverse split from officers, enforced by the same endpoint via a role→allowed-status mapping.
- Self-protection is enforced server-side: an admin cannot deactivate their own account or change their own role via the API, regardless of what the frontend allows.
- Residents are never created via the admin API — only `SUPPORT_OFFICER` and `ADMIN` accounts are admin-creatable, since residents interact with the system primarily as guests.

---

## Cross-Cutting Decisions

- **Status lifecycle:** `Submitted → Under Review → In Progress → Resolved → Closed`, with `Duplicate` and `Rejected` as terminal side-states reachable only early in the lifecycle. All transitions are validated server-side against an explicit state machine — no status can be skipped, and no backward transition is allowed.
- **Reference numbers** (format `SR-{year}-{8-char random}`) are generated at submission time and are the single mechanism by which both guests and staff can look up a request — guests have no other way to list "their" requests, since they have no account.
- **Internal notes** are private to staff (officers and admins) — residents, including the request's own submitter, can never see them.
- **Audit log** records every individual field change (who, what field, old value, new value, when) as its own row — chosen over batching multi-field changes into one row, for a simpler and more consistent forensic trail.