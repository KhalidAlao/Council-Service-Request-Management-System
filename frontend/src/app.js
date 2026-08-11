/**
 * App entry point — initializes the router and starts the application.
 */
import { initRouter, navigate } from './utils/router.js';
import { getToken, getUserRole, setUnauthorizedHandler, logout } from './api/client.js';
import { renderLogin } from './pages/login.js';
import { renderSubmit } from './pages/submit.js';
import { renderTrack } from './pages/track.js';
import { renderDashboard } from './pages/dashboard.js';
import { renderDetail } from './pages/detail.js';
import { renderAdmin } from './pages/admin.js';

// ---- Wire up 401 handling ----
setUnauthorizedHandler(() => navigate('/login'));

// ---- Render navigation header ----
function renderHeader() {
    const token = getToken();
    const role = getUserRole();
    const isLoggedIn = !!token;

    let navHtml = `
        <nav class="main-nav">
            <div class="nav-brand">Council Service Request Managment System</div>
            <ul class="nav-links">
                <li><a href="#/submit">Submit</a></li>
                <li><a href="#/track">Track</a></li>
    `;
    if (isLoggedIn) {
        navHtml += `
            <li><a href="#/dashboard">Dashboard</a></li>
        `;
        if (role === 'ADMIN') {
            navHtml += `
                <li><a href="#/admin">Admin</a></li>
            `;
        }
        navHtml += `
            <li><button id="logout-btn" class="nav-logout">Logout</button></li>
        `;
    } else {
        navHtml += `
            <li><a href="#/login">Login</a></li>
        `;
    }
    navHtml += `
            </ul>
        </nav>
    `;

    const existingNav = document.querySelector('.main-nav');
    if (existingNav) existingNav.remove();

    const headerContainer = document.createElement('div');
    headerContainer.innerHTML = navHtml;
    document.body.prepend(headerContainer.firstElementChild);

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            logout();                       
            navigate('/login');
            renderHeader();
        });
    }
}

// ---- Route registry ----
const routes = {
    '/': renderSubmit,
    '/login': renderLogin,
    '/dashboard': renderDashboard,
    '/submit': renderSubmit,
    '/track': renderTrack,
    '/detail/:id': renderDetail,
    '/admin': renderAdmin,
};

// ---- Auth guard ----
const protectedRoutes = ['/dashboard', '/detail/:id', '/admin'];

const routeGuard = (path) => {
    const isProtected = protectedRoutes.some(pattern => {
        if (pattern === path) return true;
        if (pattern === '/detail/:id' && path.startsWith('/detail/')) return true;
        return false;
    });

    if (isProtected && !getToken()) {
        navigate('/login');
        return false;
    }
    return true;
};

// ---- Custom initializer ----
function initializeApp() {
    const wrappedRoutes = {};
    for (const [path, renderFn] of Object.entries(routes)) {
        wrappedRoutes[path] = (params) => {
            renderHeader();
            renderFn(params);
        };
    }
    initRouter(wrappedRoutes, routeGuard);
}

// ---- Start the app ----
initializeApp();