/**
 * Admin page — user management (admin only).
 * View users, create staff accounts, deactivate users.
 */
import { apiCall, getToken, getUserRole, getUserId } from '../api/client.js';
import { navigate } from '../utils/router.js';
import { formatApiError } from '../utils/errors.js';

// Only SUPPORT_OFFICER and ADMIN can be created via this UI
const CREATE_ROLES = ['SUPPORT_OFFICER', 'ADMIN'];
const STATUS_OPTIONS = ['active', 'inactive']; // for filtering, optional

export function renderAdmin() {
    const app = document.getElementById('app');

    // Guard: only admin can access
    if (getUserRole() !== 'ADMIN') {
        app.innerHTML = `
            <div class="admin-container">
                <h1>Admin Access Denied</h1>
                <p>You do not have permission to view this page.</p>
                <p><a href="#/dashboard">← Back to Dashboard</a></p>
            </div>
        `;
        return;
    }

    // Render basic structure with loading state
    app.innerHTML = `
        <div class="admin-container">
            <h1>Admin — User Management</h1>

            <!-- Create user form -->
            <div class="admin-section">
                <h2>Create Staff User</h2>
                <form id="create-user-form">
                    <div class="form-group">
                        <label for="create-name">Full Name *</label>
                        <input type="text" id="create-name" required />
                    </div>
                    <div class="form-group">
                        <label for="create-email">Email *</label>
                        <input type="email" id="create-email" required />
                    </div>
                    <div class="form-group">
                        <label for="create-password">Password * (min 8 characters)</label>
                        <input type="password" id="create-password" required minlength="8" />
                    </div>
                    <div class="form-group">
                        <label for="create-role">Role *</label>
                        <select id="create-role" required>
                            <option value="">-- Select --</option>
                            ${CREATE_ROLES.map(r => `<option value="${r}">${r}</option>`).join('')}
                        </select>
                    </div>
                    <div id="create-department-group" class="form-group" style="display:none;">
                        <label for="create-department">Department (required for Support Officer)</label>
                        <select id="create-department">
                            <option value="">-- Select --</option>
                            <!-- populated by fetchDepartments() -->
                        </select>
                    </div>
                    <div id="create-error" class="error-message" style="display:none;"></div>
                    <div id="create-success" class="success-message" style="display:none;"></div>
                    <button type="submit" class="btn btn-primary">Create User</button>
                </form>
            </div>

            <!-- User list -->
            <div class="admin-section">
                <h2>All Users</h2>
                <div id="user-list-loading">Loading users...</div>
                <div id="user-list-error" class="error-message" style="display:none;"></div>
                <div id="user-list-container"></div>
            </div>
        </div>
    `;

    // Populate department dropdown (fetch departments from API)
    const deptSelect = document.getElementById('create-department');
    fetchDepartments(deptSelect);

    // Role toggle for department field
    const roleSelect = document.getElementById('create-role');
    const deptGroup = document.getElementById('create-department-group');
    if (roleSelect) {
        roleSelect.addEventListener('change', () => {
            const val = roleSelect.value;
            deptGroup.style.display = (val === 'SUPPORT_OFFICER') ? 'block' : 'none';
        });
        // Trigger initial state (in case of pre-filled)
        roleSelect.dispatchEvent(new Event('change'));
    }

    // Form submission
    const form = document.getElementById('create-user-form');
    const errorEl = document.getElementById('create-error');
    const successEl = document.getElementById('create-success');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorEl.style.display = 'none';
        successEl.style.display = 'none';

        const name = document.getElementById('create-name').value.trim();
        const email = document.getElementById('create-email').value.trim();
        const password = document.getElementById('create-password').value;
        const role = document.getElementById('create-role').value;
        const departmentId = document.getElementById('create-department').value;

        // Basic validation
        if (!name || !email || !password || !role) {
            errorEl.textContent = 'Please fill in all required fields.';
            errorEl.style.display = 'block';
            return;
        }
        if (role === 'SUPPORT_OFFICER' && !departmentId) {
            errorEl.textContent = 'Please select a department for Support Officer.';
            errorEl.style.display = 'block';
            return;
        }

        const payload = {
            full_name: name,
            email,
            password,
            role,
        };
        if (role === 'SUPPORT_OFFICER') {
            payload.department_id = parseInt(departmentId, 10);
        }

        try {
            const response = await apiCall('/admin/users', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            const data = await response.json();

            if (!response.ok) {
                const msg = formatApiError(data.error || data);
                errorEl.textContent = msg;
                errorEl.style.display = 'block';
                return;
            }

            successEl.textContent = `User "${data.full_name}" created successfully!`;
            successEl.style.display = 'block';
            form.reset();
            // Reset department visibility
            roleSelect.dispatchEvent(new Event('change'));
            // Re-fetch user list
            fetchUserList();
        } catch (err) {
            errorEl.textContent = 'Network error: ' + err.message;
            errorEl.style.display = 'block';
        }
    });

    // Fetch and render user list
    fetchUserList();
}

// ---- Fetch departments ----
async function fetchDepartments(selectEl) {
    try {
        const token = getToken();
        const response = await fetch('/api/v1/admin/departments', {  
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) {
            console.warn('Could not fetch departments');
            return;
        }
        const data = await response.json();
        if (data && data.length > 0) {
            selectEl.innerHTML = '<option value="">-- Select --</option>' +
                data.map(d => `<option value="${d.department_id}">${d.name}</option>`).join('');
        }
    } catch (e) {
        console.warn('Failed to load departments:', e);
    }
}

// ---- Fetch and render user list ----
async function fetchUserList() {
    const container = document.getElementById('user-list-container');
    const loading = document.getElementById('user-list-loading');
    const errorEl = document.getElementById('user-list-error');

    loading.style.display = 'block';
    errorEl.style.display = 'none';
    container.innerHTML = '';

    try {
        const response = await apiCall('/admin/users');
        const data = await response.json();

        if (!response.ok) {
            errorEl.textContent = formatApiError(data.error || data);
            errorEl.style.display = 'block';
            loading.style.display = 'none';
            return;
        }

        const users = data.data || [];
        if (users.length === 0) {
            container.innerHTML = '<p>No users found.</p>';
            loading.style.display = 'none';
            return;
        }

        const currentUserId = getUserId();

        let tableHtml = `
            <table class="admin-users-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Department</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const user of users) {
            const isSelf = user.user_id == currentUserId;
            const isActive = user.is_active;
            const deptName = user.department_name || '—';
            const statusLabel = isActive ? 'Active' : 'Inactive';
            const statusClass = isActive ? 'status-active' : 'status-inactive';

            tableHtml += `
                <tr>
                    <td>${user.user_id}</td>
                    <td>${user.full_name}</td>
                    <td>${user.email}</td>
                    <td>${user.role}</td>
                    <td>${deptName}</td>
                    <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                    <td>
                        ${isActive && !isSelf ? `<button class="btn btn-danger deactivate-btn" data-user-id="${user.user_id}">Deactivate</button>` : 
                          isActive && isSelf ? '—' : '—'}
                    </td>
                </tr>
            `;
        }

        tableHtml += `</tbody></table>`;
        container.innerHTML = tableHtml;

        // Attach deactivate event listeners
        document.querySelectorAll('.deactivate-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const userId = btn.dataset.userId;
                if (confirm(`Deactivate user ID ${userId}?`)) {
                    await deactivateUser(userId);
                }
            });
        });

        loading.style.display = 'none';
    } catch (err) {
        errorEl.textContent = 'Network error: ' + err.message;
        errorEl.style.display = 'block';
        loading.style.display = 'none';
    }
}

// ---- Deactivate a user ----
async function deactivateUser(userId) {
    try {
        const response = await apiCall(`/admin/users/${userId}/deactivate`, {
            method: 'PATCH',
            body: JSON.stringify({}), // empty body
        });
        const data = await response.json();

        if (!response.ok) {
            alert('Deactivation failed: ' + formatApiError(data.error || data));
            return;
        }

        alert('User deactivated successfully.');
        // Refresh list
        fetchUserList();
    } catch (err) {
        alert('Network error: ' + err.message);
    }
}