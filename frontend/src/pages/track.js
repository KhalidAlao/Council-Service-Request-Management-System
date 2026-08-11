/**
 * Track page — public request tracking by reference number.
 */
import { apiCall } from '../api/client.js';
import { formatApiError } from '../utils/errors.js';

export function renderTrack() {
    const app = document.getElementById('app');

    app.innerHTML = `
        <div class="track-container">
            <h1>Track Your Request</h1>
            <p>Enter the reference number you received after submitting.</p>
            <form id="track-form">
                <div class="form-group">
                    <label for="reference">Reference Number</label>
                    <input type="text" id="reference" name="reference" placeholder="e.g., SR-2026-A7X92B" required />
                </div>
                <div id="track-error" class="error-message" style="display:none;"></div>
                <button type="submit">Track</button>
            </form>
            <div id="track-result" style="display:none;">
                <h2>Request Status</h2>
                <table class="track-details">
                    <tbody>
                        <tr><td><strong>Status</strong></td><td id="track-status"></td></tr>
                        <tr><td><strong>Title</strong></td><td id="track-title"></td></tr>
                        <tr><td><strong>Category</strong></td><td id="track-category"></td></tr>
                        <tr><td><strong>Location</strong></td><td id="track-location"></td></tr>
                        <tr><td><strong>Submitted</strong></td><td id="track-submitted"></td></tr>
                        <tr><td><strong>Last Updated</strong></td><td id="track-updated"></td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;

    const form = document.getElementById('track-form');
    const errorEl = document.getElementById('track-error');
    const resultEl = document.getElementById('track-result');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        errorEl.style.display = 'none';
        errorEl.textContent = '';
        resultEl.style.display = 'none';

        const reference = document.getElementById('reference').value.trim();

        if (!reference) {
            errorEl.textContent = 'Please enter a reference number.';
            errorEl.style.display = 'block';
            return;
        }

        try {
            const response = await apiCall(`/requests/track?reference=${encodeURIComponent(reference)}`, {
                method: 'GET',
            });

            if (response.status === 404) {
                errorEl.textContent = 'No request found with that reference number.';
                errorEl.style.display = 'block';
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                const msg = formatApiError(data.error || data);
                errorEl.textContent = msg;
                errorEl.style.display = 'block';
                return;
            }

            // Populate result
            document.getElementById('track-status').textContent = data.status || '—';
            document.getElementById('track-title').textContent = data.title || '—';
            document.getElementById('track-category').textContent = data.category || '—';
            document.getElementById('track-location').textContent = data.location || '—';
            document.getElementById('track-submitted').textContent = data.date_submitted ? new Date(data.date_submitted).toLocaleString() : '—';
            document.getElementById('track-updated').textContent = data.last_updated ? new Date(data.last_updated).toLocaleString() : '—';

            resultEl.style.display = 'block';
        } catch (err) {
            errorEl.textContent = 'Network error. Please try again.';
            errorEl.style.display = 'block';
        }
    });
}