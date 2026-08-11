/**
 * Dashboard — list, filter, and paginate requests.
 * Staff-only page (officers/admins).
 */
import { apiCall } from '../api/client.js';
import { navigate } from '../utils/router.js';
import { formatApiError } from '../utils/errors.js';

const STATUSES = ['SUBMITTED', 'UNDER_REVIEW', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'];
const CATEGORIES = ['ROADS', 'WASTE', 'PARKS', 'STREET_LIGHTING', 'BUILDINGS', 'OTHER'];
const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'URGENT'];

// State
let currentPage = 1;
let totalPages = 1;
let filters = {
    status: '',
    category: '',
    priority: '',
    // date_from/date_to can be added later
};

export function renderDashboard() {
    const app = document.getElementById('app');

    app.innerHTML = `
        <div class="dashboard-container">
            <h1>Requests Dashboard</h1>

            <!-- Filter Bar -->
            <div class="filter-bar">
                <div class="filter-group">
                    <label for="filter-status">Status</label>
                    <select id="filter-status">
                        <option value="">All</option>
                        ${STATUSES.map(s => `<option value="${s}">${s}</option>`).join('')}
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-category">Category</label>
                    <select id="filter-category">
                        <option value="">All</option>
                        ${CATEGORIES.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-priority">Priority</label>
                    <select id="filter-priority">
                        <option value="">All</option>
                        ${PRIORITIES.map(p => `<option value="${p}">${p}</option>`).join('')}
                    </select>
                </div>
                <button id="apply-filters" class="btn btn-primary">Apply Filters</button>
                <button id="clear-filters" class="btn btn-secondary">Clear</button>
            </div>

            <!-- Loading / Error -->
            <div id="dashboard-loading" style="display:none;">Loading...</div>
            <div id="dashboard-error" class="error-message" style="display:none;"></div>

            <!-- Results -->
            <div id="requests-list"></div>

            <!-- Pagination -->
            <div class="pagination-controls">
                <button id="prev-page" class="btn btn-secondary" disabled>Previous</button>
                <span id="page-info">Page 1 of 1</span>
                <button id="next-page" class="btn btn-secondary" disabled>Next</button>
            </div>
        </div>
    `;

    // Load initial data
    fetchRequests();

    // --- Event listeners ---
    document.getElementById('apply-filters').addEventListener('click', () => {
        currentPage = 1;
        filters.status = document.getElementById('filter-status').value;
        filters.category = document.getElementById('filter-category').value;
        filters.priority = document.getElementById('filter-priority').value;
        fetchRequests();
    });

    document.getElementById('clear-filters').addEventListener('click', () => {
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-category').value = '';
        document.getElementById('filter-priority').value = '';
        currentPage = 1;
        filters = { status: '', category: '', priority: '' };
        fetchRequests();
    });

    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            fetchRequests();
        }
    });

    document.getElementById('next-page').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            fetchRequests();
        }
    });
}

async function fetchRequests() {
    const loadingEl = document.getElementById('dashboard-loading');
    const errorEl = document.getElementById('dashboard-error');
    const listEl = document.getElementById('requests-list');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');

    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    listEl.innerHTML = '';

    try {
        // Build query string
        const params = new URLSearchParams();
        params.set('page', currentPage);
        params.set('limit', 20);
        if (filters.status) params.set('status', filters.status);
        if (filters.category) params.set('category', filters.category);
        if (filters.priority) params.set('priority', filters.priority);

        const response = await apiCall(`/requests?${params.toString()}`);
        const data = await response.json();

        if (!response.ok) {
            const msg = formatApiError(data.error || data);
            errorEl.textContent = msg;
            errorEl.style.display = 'block';
            return;
        }

        // Update pagination
        totalPages = data.pagination?.total_pages || 1;
        pageInfo.textContent = `Page ${data.pagination?.page || 1} of ${totalPages}`;
        prevBtn.disabled = currentPage <= 1;
        nextBtn.disabled = currentPage >= totalPages;

        // Render table
        if (!data.data || data.data.length === 0) {
            listEl.innerHTML = `<p>No requests found.</p>`;
            return;
        }

        let tableHtml = `
            <table class="requests-table">
                <thead>
                    <tr>
                        <th>Reference</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Category</th>
                        <th>Assigned</th>
                        <th>Submitted</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const req of data.data) {
            const assignedName = req.assigned_officer?.full_name || 'Unassigned';
            const submittedDate = new Date(req.date_submitted).toLocaleDateString();
            tableHtml += `
                <tr class="clickable-row" data-id="${req.request_id}">
                    <td><strong>${req.reference_number}</strong></td>
                    <td>${req.title}</td>
                    <td><span class="status-badge status-${req.status}">${req.status}</span></td>
                    <td><span class="priority-badge priority-${req.priority}">${req.priority}</span></td>
                    <td>${req.category}</td>
                    <td>${assignedName}</td>
                    <td>${submittedDate}</td>
                </tr>
            `;
        }

        tableHtml += `</tbody></table>`;
        listEl.innerHTML = tableHtml;

        // Click row → navigate to detail
        document.querySelectorAll('.clickable-row').forEach(row => {
            row.addEventListener('click', () => {
                const id = row.dataset.id;
                navigate(`/detail/${id}`);
            });
        });

    } catch (err) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    } finally {
        loadingEl.style.display = 'none';
    }
}