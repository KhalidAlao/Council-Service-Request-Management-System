/**
 * Submit page — guest or authenticated request submission.
 */
import { apiCall, getToken } from '../api/client.js';
import { navigate } from '../utils/router.js';
import { formatApiError } from '../utils/errors.js';

const CATEGORIES = ['ROADS', 'WASTE', 'PARKS', 'STREET_LIGHTING', 'BUILDINGS', 'OTHER'];

export function renderSubmit() {
    const app = document.getElementById('app');
    const isAuthenticated = !!getToken();

    app.innerHTML = `
        <div class="submit-container">
            <h1>Submit a Service Request</h1>
            <form id="submit-form">
                <div class="form-group">
                    <label for="title">Title *</label>
                    <input type="text" id="title" name="title" required />
                </div>
                <div class="form-group">
                    <label for="description">Description *</label>
                    <textarea id="description" name="description" rows="4" required></textarea>
                </div>
                <div class="form-group">
                    <label for="location">Location *</label>
                    <input type="text" id="location" name="location" required />
                </div>
                <div class="form-group">
                    <label for="category">Category *</label>
                    <select id="category" name="category" required>
                        <option value="">-- Select --</option>
                        ${CATEGORIES.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                </div>

                ${isAuthenticated ? '' : `
                    <div class="guest-fields">
                        <hr />
                        <p><strong>You are submitting as a guest.</strong> Please provide your contact details.</p>
                        <div class="form-group">
                            <label for="guest_name">Full Name *</label>
                            <input type="text" id="guest_name" name="guest_name" required />
                        </div>
                        <div class="form-group">
                            <label for="guest_email">Email *</label>
                            <input type="email" id="guest_email" name="guest_email" required />
                        </div>
                        <div class="form-group">
                            <label for="guest_phone">Phone *</label>
                            <input type="tel" id="guest_phone" name="guest_phone" required />
                        </div>
                    </div>
                `}

                <div id="submit-error" class="error-message" style="display:none;"></div>
                <button type="submit">Submit Request</button>
            </form>
            <div id="submit-result" style="display:none;" class="success-message">
                <p>✅ Your request has been submitted.</p>
                <p><strong>Reference Number:</strong> <span id="ref-number"></span></p>
                <p>You can use this number to track your request.</p>
            </div>
        </div>
    `;

    const form = document.getElementById('submit-form');
    const errorEl = document.getElementById('submit-error');
    const resultEl = document.getElementById('submit-result');
    const refSpan = document.getElementById('ref-number');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        errorEl.style.display = 'none';
        errorEl.textContent = '';
        resultEl.style.display = 'none';

        const formData = new FormData(form);
        const payload = {
            title: formData.get('title'),
            description: formData.get('description'),
            location: formData.get('location'),
            category: formData.get('category'),
        };

        if (!isAuthenticated) {
            payload.guest_name = formData.get('guest_name');
            payload.guest_email = formData.get('guest_email');
            payload.guest_phone = formData.get('guest_phone');
        }

        try {
            const response = await apiCall('/requests', {
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

            // Success: show reference number
            refSpan.textContent = data.reference_number;
            resultEl.style.display = 'block';
            form.reset();

            // Optionally scroll to result
            resultEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch (err) {
            errorEl.textContent = 'Network error. Please try again.';
            errorEl.style.display = 'block';
        }
    });
}