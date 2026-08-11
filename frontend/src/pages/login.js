/**
 * Login page — renders a form and handles authentication.
 */
import { apiCall, setToken, setUserRole, setUserId } from '../api/client.js';
import { navigate } from '../utils/router.js';

export function renderLogin() {
    const app = document.getElementById('app');

    app.innerHTML = `
        <div class="login-container">
            <h1>Council Service Management</h1>
            <h2>Login</h2>
            <form id="login-form">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required placeholder="admin@council.gov" />
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required placeholder="••••••••" />
                </div>
                <div id="login-error" class="error-message" style="display:none;"></div>
                <button type="submit">Log in</button>
            </form>
        </div>
    `;

    const form = document.getElementById('login-form');
    const errorEl = document.getElementById('login-error');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        errorEl.style.display = 'none';
        errorEl.textContent = '';

        try {
            const response = await apiCall('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                const msg = data.error || data.message || 'Login failed';
                errorEl.textContent = msg;
                errorEl.style.display = 'block';
                return;
            }

            // Store token and user info
            setToken(data.access_token);
            if (data.user) {
                if (data.user.role) setUserRole(data.user.role);
                if (data.user.user_id) setUserId(String(data.user.user_id));
            }

            navigate('/dashboard');
        } catch (err) {
            errorEl.textContent = 'Network error. Please try again.';
            errorEl.style.display = 'block';
        }
    });
}