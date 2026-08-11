/**
 * API client with token management and automatic 401 handling.
 */

const API_BASE = '/api/v1';

let onUnauthorized = null;

/**
 * Set a callback to be called when a 401 response is received.
 */
export function setUnauthorizedHandler(handler) {
    onUnauthorized = handler;
}

/**
 * Store the JWT token in localStorage.
 */
export function setToken(token) {
    if (token) {
        localStorage.setItem('access_token', token);
    } else {
        localStorage.removeItem('access_token');
    }
}

/**
 * Retrieve the stored JWT token.
 */
export function getToken() {
    return localStorage.getItem('access_token');
}

/**
 * Remove the token (logout).
 */
export function logout() {
    setToken(null);
    setUserRole(null);
    setUserId(null);
    if (onUnauthorized) onUnauthorized();
}

/**
 * Make an authenticated API call.
 * @param {string} endpoint - e.g., '/requests'
 * @param {object} options - fetch options (method, body, headers, etc.)
 * @returns {Promise<Response>} the fetch Response object
 */
export async function apiCall(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...(options.headers || {})
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    // Handle 401 Unauthorized globally
    if (response.status === 401) {
        logout();
        // Optionally navigate to login (handled by the caller via onUnauthorized)
        return response;
    }

    return response;
}

/**
 * Store the user's role in localStorage.
 */
export function setUserRole(role) {
    if (role) {
        localStorage.setItem('user_role', role);
    } else {
        localStorage.removeItem('user_role');
    }
}

/**
 * Retrieve the stored user role.
 */
export function getUserRole() {
    return localStorage.getItem('user_role');
}

/**
 * Store the user's ID in localStorage.
 */
export function setUserId(id) {
    if (id) {
        localStorage.setItem('user_id', id);
    } else {
        localStorage.removeItem('user_id');
    }
}

/**
 * Retrieve the stored user ID.
 */
export function getUserId() {
    return localStorage.getItem('user_id');
}