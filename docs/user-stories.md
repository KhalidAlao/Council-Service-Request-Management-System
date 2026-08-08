# Council Service Management System - User Stories

This document contains the Gherkin-style user stories that define the core workflow and permission rules for the system.

---

## Story 1: Support Officer Status Permissions

**As a** Support Officer,  
**I want to** control only the "Under Review" and "In Progress" statuses,  
**So that** I can triage requests appropriately without accidentally closing them.

```gherkin
Scenario: Support Officer attempts to update a request status
  Given a logged-in user with the role "Support Officer"
  And a service request exists with the status "Submitted"
  When the Support Officer changes the request status to "Under Review"
  Then the system accepts the change and updates the status to "Under Review"
  And the Support Officer can change the status to "In Progress"
  But when the Support Officer attempts to change the status to "Resolved" or "Closed"
  Then the system denies the action and displays a permission error
```

---

## Story 2: Admin Status Permissions

**As an** Admin,  
**I want to** control only the "Resolved" and "Closed" statuses,  
**So that** I can finalize requests and ensure only authorised staff close tickets.

```gherkin
Scenario: Admin attempts to finalize a request status
  Given a logged-in user with the role "Admin"
  And a service request exists with the status "In Progress"
  When the Admin changes the request status to "Resolved"
  Then the system accepts the change and updates the status to "Resolved"
  And the Admin can change the status to "Closed"
  But when the Admin attempts to change the status to "Under Review" or "In Progress"
  Then the system denies the action and displays a permission error
```

---

## Story 3: Full Workflow – Under Review → Notify Department → In Progress

**As a** Support Officer,  
**I want to** notify the relevant department when a request is placed under review, and only move it to "In Progress" once they confirm feasibility,  
**So that** I ensure work is only started when the department is ready and able to act.

```gherkin
Scenario: Support Officer initiates department analysis and moves request to progress
  Given a service request exists with the status "Submitted"
  And the request falls under the jurisdiction of a specific department
  When the Support Officer moves the request to "Under Review"
  Then the system updates the status to "Under Review"
  And the Support Officer sends a message to the relevant department to analyze the request

  Given the department has analyzed the request
  When the department confirms that working on the request is now possible
  Then the system alerts the Support Officer with a feasibility confirmation

  When the Support Officer receives the alert
  And the Support Officer moves the request to "In Progress"
  Then the system updates the request to "In Progress"
```

---

## Story 4: Assigning an Officer (Admin vs Officer Permissions)

**As an** Admin,  
**I want to** assign any request to any officer; as a Support Officer, I can only self-assign unassigned requests or hand off requests currently assigned to me,  
**So that** assignments are controlled and handoffs are managed properly.

```gherkin
Scenario: Admin assigns a request to an officer
  Given a logged-in user with the role "Admin"
  And a service request exists with no assigned officer
  When the Admin assigns the request to any officer
  Then the system updates the assigned_officer_id

Scenario: Officer self-assigns an unassigned request
  Given a logged-in user with the role "Support Officer"
  And a service request exists with assigned_officer_id = NULL
  When the Officer assigns the request to themselves
  Then the system accepts the assignment

Scenario: Officer attempts to assign an unassigned request to another officer
  Given a logged-in user with the role "Support Officer"
  And a service request exists with assigned_officer_id = NULL
  When the Officer attempts to assign the request to a different officer
  Then the system denies the action with a permission error

Scenario: Officer hands off a request assigned to them
  Given a logged-in user with the role "Support Officer"
  And a service request exists with assigned_officer_id = current_user
  When the Officer reassigns the request to a colleague
  Then the system accepts the reassignment
```

---

## Story 5: Guest Submission and Tracking

**As a** guest resident,  
**I want to** submit a request without creating an account and later track its status using a reference number,  
**So that** I can report issues quickly and stay informed.

```gherkin
Scenario: Guest submits a request
  Given a guest user with no authentication token
  When the guest submits a request with valid guest_name, guest_email, and guest_phone
  Then the system creates a service request with submitted_by_user_id = NULL
  And the system generates a unique reference number

Scenario: Guest tracks a request by reference number
  Given a service request exists with a reference number
  When the guest queries the tracking endpoint with that reference
  Then the system returns the current status and basic details
  And the endpoint is rate-limited to 10 requests per minute
```

---


