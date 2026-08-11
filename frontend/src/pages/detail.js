/**
 * Request Detail page — view, status change, assignment, notes, audit log.
 */
import { apiCall, getToken, getUserRole, getUserId } from '../api/client.js';
import { navigate } from '../utils/router.js';
import { formatApiError } from '../utils/errors.js';

const OFFICER_STATUSES = ['UNDER_REVIEW', 'IN_PROGRESS', 'DUPLICATE', 'REJECTED'];
const ADMIN_STATUSES = ['RESOLVED', 'CLOSED'];

export function renderDetail(params) {
    const id = params.id;
    const app = document.getElementById('app');

    if (!id || isNaN(parseInt(id, 10))) {
        document.getElementById('app').innerHTML = `
            <div class="detail-container">
                <h1>Invalid Request</h1>
                <p>The request ID is missing or invalid.</p>
                <p><a href="#/dashboard">← Back to Dashboard</a></p>
            </div>
        `;
        return;
    }

    // Show loading
    app.innerHTML = `
        <div class="detail-container">
            <h1>Request Detail</h1>
            <p>Loading...</p>
            <p><a href="#/dashboard">← Back to Dashboard</a></p>
        </div>
    `;

    Promise.all([
        apiCall(`/requests/${id}`),
        apiCall(`/requests/${id}/notes`),
        apiCall(`/requests/${id}/audit`)
    ])
    .then(async ([requestRes, notesRes, auditRes]) => {
        const requestData = await requestRes.json();
        const notesData = await notesRes.json();
        const auditData = await auditRes.json();

        if (!requestRes.ok) {
            app.innerHTML = `
                <div class="detail-container">
                    <h1>Request Detail</h1>
                    <p class="error-message">${formatApiError(requestData.error || requestData)}</p>
                    <p><a href="#/dashboard">← Back to Dashboard</a></p>
                </div>
            `;
            return;
        }

        if (!requestData.request_id) {
            app.innerHTML = `
                <div class="detail-container">
                    <h1>Request Detail</h1>
                    <p>Request not found.</p>
                    <p><a href="#/dashboard">← Back to Dashboard</a></p>
                </div>
            `;
            return;
        }

        renderFullDetail(requestData, notesData, auditData, id);
    })
    .catch(err => {
        app.innerHTML = `
            <div class="detail-container">
                <h1>Request Detail</h1>
                <p class="error-message">Network error: ${err.message}</p>
                <p><a href="#/dashboard">← Back to Dashboard</a></p>
            </div>
        `;
    });
}

function renderFullDetail(request, notes, audit, id) {
    const app = document.getElementById('app');
    const role = getUserRole();
    const userId = getUserId();

    const fmt = (d) => d ? new Date(d).toLocaleString() : '—';

    let html = `
        <div class="detail-container">
            <h1>Request Detail</h1>
            <p><a href="#/dashboard">← Back to Dashboard</a></p>

            <div class="detail-card">
                <div class="detail-header">
                    <h2>${request.title || 'Untitled'}</h2>
                    <span class="status-badge status-${request.status}">${request.status}</span>
                </div>
                <div class="detail-body">
                    <div class="detail-row"><strong>Reference:</strong> ${request.reference_number}</div>
                    <div class="detail-row"><strong>Category:</strong> ${request.category}</div>
                    <div class="detail-row"><strong>Priority:</strong> ${request.priority}</div>
                    <div class="detail-row"><strong>Location:</strong> ${request.location}</div>
                    <div class="detail-row"><strong>Description:</strong> ${request.description || '—'}</div>
                    <div class="detail-row"><strong>Submitted:</strong> ${fmt(request.date_submitted)}</div>
                    <div class="detail-row"><strong>Last Updated:</strong> ${fmt(request.last_updated)}</div>
                    <div class="detail-row"><strong>Submitted By:</strong> ${request.submitted_by?.full_name || request.guest_name || 'Guest'}</div>
                    <div class="detail-row"><strong>Assigned Officer:</strong> ${request.assigned_officer?.full_name || 'Unassigned'}</div>
                    ${request.rejection_reason ? `<div class="detail-row"><strong>Rejection Reason:</strong> ${request.rejection_reason}</div>` : ''}
                </div>
            </div>

            <!-- Status Control -->
            <div class="detail-section">
                <h3>Change Status</h3>
                <div id="status-control">
                    ${buildStatusControl(request.status, role)}
                </div>
                <div id="status-message" class="status-message" style="display:none;"></div>
            </div>

            <!-- Assignment Control -->
            <div class="detail-section">
                <h3>Assignment</h3>
                <div id="assignment-control">
                    ${buildAssignmentControl(request.assigned_officer?.user_id, role, userId)}
                </div>
                <div id="assignment-message" class="status-message" style="display:none;"></div>
            </div>

            <!-- Notes -->
            <div class="detail-section">
                <h3>Notes</h3>
                <div id="notes-list">
                    ${notes && notes.length > 0 ? notes.map(n => `
                        <div class="note-item">
                            <div class="note-meta">${n.author?.full_name || 'Unknown'} — ${fmt(n.created_at)}</div>
                            <div class="note-body">${n.body}</div>
                        </div>
                    `).join('') : '<p>No notes yet.</p>'}
                </div>
                <div class="add-note">
                    <textarea id="note-input" placeholder="Add a note..." rows="2"></textarea>
                    <button id="add-note-btn" class="btn btn-primary">Add Note</button>
                </div>
                <div id="note-message" class="status-message" style="display:none;"></div>
            </div>

            <!-- Audit Log -->
            <div class="detail-section">
                <h3>Audit Log</h3>
                <div id="audit-log">
                    ${audit && audit.data && audit.data.length > 0 ? audit.data.map(entry => `
                        <div class="audit-entry">
                            <span class="audit-field">${entry.field_changed}</span>
                            <span class="audit-old">${entry.old_value ?? '—'}</span>
                            → <span class="audit-new">${entry.new_value ?? '—'}</span>
                            <span class="audit-meta">by ${entry.changed_by?.full_name || 'Unknown'} at ${fmt(entry.changed_at)}</span>
                        </div>
                    `).join('') : '<p>No audit entries.</p>'}
                </div>
            </div>
        </div>
    `;

    app.innerHTML = html;

    // ---- Status dropdown toggles extra fields ----
    const statusControl = document.getElementById('status-control');
    if (statusControl) {
        const statusSelect = statusControl.querySelector('.status-select');
        const dupField = document.getElementById('duplicate-field');
        const rejField = document.getElementById('reject-field');
        if (statusSelect) {
            statusSelect.addEventListener('change', () => {
                const val = statusSelect.value;
                if (dupField) dupField.style.display = (val === 'DUPLICATE') ? 'block' : 'none';
                if (rejField) rejField.style.display = (val === 'REJECTED') ? 'block' : 'none';
            });
            // Trigger initial state
            statusSelect.dispatchEvent(new Event('change'));
        }
    }

    // ---- Status change submit ----
    const statusMsg = document.getElementById('status-message');
    const statusSubmit = document.querySelector('.status-submit');
    if (statusSubmit) {
        statusSubmit.addEventListener('click', async () => {
            const statusControl = document.getElementById('status-control');
            const select = statusControl.querySelector('.status-select');
            const targetStatus = select?.value;
            if (!targetStatus) return;

            let payload = { status: targetStatus };

            // DUPLICATE handling — use specific selector
            if (targetStatus === 'DUPLICATE') {
                const dupInput = document.querySelector('#duplicate-field input');
                const dupId = dupInput?.value;
                if (!dupId) {
                    statusMsg.textContent = 'Please enter the duplicate request ID.';
                    statusMsg.style.display = 'block';
                    return;
                }
                payload.duplicate_of_request_id = parseInt(dupId, 10);
            }
            // REJECTED handling — use specific selector
            else if (targetStatus === 'REJECTED') {
                const rejInput = document.querySelector('#reject-field input');
                const reason = rejInput?.value;
                if (!reason || !reason.trim()) {
                    statusMsg.textContent = 'Please enter a rejection reason.';
                    statusMsg.style.display = 'block';
                    return;
                }
                payload.rejection_reason = reason.trim();
            }

            statusMsg.style.display = 'none';
            try {
                const response = await apiCall(`/requests/${id}/status`, {
                    method: 'PATCH',
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (!response.ok) {
                    statusMsg.textContent = formatApiError(data.error || data);
                    statusMsg.style.display = 'block';
                    return;
                }
                statusMsg.textContent = 'Status updated successfully!';
                statusMsg.style.color = 'green';
                statusMsg.style.display = 'block';
                renderDetail({ id });
            } catch (err) {
                statusMsg.textContent = 'Network error: ' + err.message;
                statusMsg.style.display = 'block';
            }
        });
    }

    // ---- Assignment ----
    const assignmentControl = document.getElementById('assignment-control');
    const assignMsg = document.getElementById('assignment-message');
    if (assignmentControl) {
        const assignBtn = assignmentControl.querySelector('.assign-btn');
        if (assignBtn) {
            assignBtn.addEventListener('click', async () => {
                let targetId;
                const input = assignmentControl.querySelector('.assign-input');
                if (input) {
                    targetId = parseInt(input.value, 10);
                    if (!targetId) {
                        assignMsg.textContent = 'Please enter a valid officer ID.';
                        assignMsg.style.display = 'block';
                        return;
                    }
                } else {
                    // "Assign to me" button
                    targetId = parseInt(userId, 10);
                    if (!targetId) {
                        assignMsg.textContent = 'Unable to determine your user ID.';
                        assignMsg.style.display = 'block';
                        return;
                    }
                }

                assignMsg.style.display = 'none';
                try {
                    const response = await apiCall(`/requests/${id}/assign`, {
                        method: 'PATCH',
                        body: JSON.stringify({ assigned_officer_id: targetId }),
                    });
                    const data = await response.json();
                    if (!response.ok) {
                        assignMsg.textContent = formatApiError(data.error || data);
                        assignMsg.style.display = 'block';
                        return;
                    }
                    assignMsg.textContent = 'Assignment updated successfully!';
                    assignMsg.style.color = 'green';
                    assignMsg.style.display = 'block';
                    renderDetail({ id });
                } catch (err) {
                    assignMsg.textContent = 'Network error: ' + err.message;
                    assignMsg.style.display = 'block';
                }
            });
        }
    }

    // ---- Add note ----
    const noteInput = document.getElementById('note-input');
    const addNoteBtn = document.getElementById('add-note-btn');
    const noteMsg = document.getElementById('note-message');
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', async () => {
            const body = noteInput.value.trim();
            if (!body) {
                noteMsg.textContent = 'Please enter a note.';
                noteMsg.style.display = 'block';
                return;
            }
            noteMsg.style.display = 'none';
            try {
                const response = await apiCall(`/requests/${id}/notes`, {
                    method: 'POST',
                    body: JSON.stringify({ body }),
                });
                const data = await response.json();
                if (!response.ok) {
                    noteMsg.textContent = formatApiError(data.error || data);
                    noteMsg.style.display = 'block';
                    return;
                }
                noteMsg.textContent = 'Note added!';
                noteMsg.style.color = 'green';
                noteMsg.style.display = 'block';
                noteInput.value = '';
                renderDetail({ id });
            } catch (err) {
                noteMsg.textContent = 'Network error: ' + err.message;
                noteMsg.style.display = 'block';
            }
        });
    }
}

// ---- Helper: Build status control HTML ----
function buildStatusControl(currentStatus, role) {
    let options = [];
    if (role === 'SUPPORT_OFFICER') {
        options = OFFICER_STATUSES;
    } else if (role === 'ADMIN') {
        options = ADMIN_STATUSES;
    } else {
        return '<p>You do not have permission to change status.</p>';
    }

    const selected = options.includes(currentStatus) ? currentStatus : '';
    let html = `
        <select class="status-select">
            <option value="">-- Select status --</option>
            ${options.map(s => `<option value="${s}" ${s === selected ? 'selected' : ''}>${s}</option>`).join('')}
        </select>
    `;

    // Extra fields (toggled by event listener)
    html += `<div class="status-extra-container" style="margin-top: 8px;">`;
    html += `<div id="duplicate-field" style="display:none;">
                <label>Duplicate Request ID: <input type="number" class="status-extra-input" placeholder="Request ID" /></label>
            </div>`;
    html += `<div id="reject-field" style="display:none;">
                <label>Rejection Reason: <input type="text" class="status-extra-input" placeholder="Reason" /></label>
            </div>`;
    html += `</div>`;

    html += `<button class="status-submit btn btn-primary" style="margin-top: 8px;">Apply Status</button>`;

    return html;
}

// ---- Helper: Build assignment control HTML ----
function buildAssignmentControl(currentAssigneeId, role, userId) {
    if (role === 'SUPPORT_OFFICER') {
        return `<button class="assign-btn btn btn-primary">Assign to Me</button>`;
    } else if (role === 'ADMIN') {
        return `
            <div style="display:flex; gap:8px; align-items:center;">
                <input type="number" class="assign-input" placeholder="Officer ID" value="${currentAssigneeId || ''}" />
                <button class="assign-btn btn btn-primary">Assign</button>
            </div>
        `;
    } else {
        return '<p>You do not have permission to assign.</p>';
    }
}