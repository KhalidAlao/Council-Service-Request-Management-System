/**
 * Hash-based router with route registration, navigation, and path parameters.
 */

let routes = {};
let routeGuard = null;
let currentPath = '';

function matchRoute(pattern, path) {
    const patternParts = pattern.split('/').filter(Boolean);
    const pathParts = path.split('/').filter(Boolean);

    // Debug: log what we're matching
    console.debug('matchRoute:', { pattern, path, patternParts, pathParts });

    if (patternParts.length !== pathParts.length) {
        return null;
    }

    const params = {};
    for (let i = 0; i < patternParts.length; i++) {
        const patternPart = patternParts[i];
        const pathPart = pathParts[i];

        if (patternPart.startsWith(':')) {
            const paramName = patternPart.slice(1);
            params[paramName] = pathPart;
        } else if (patternPart !== pathPart) {
            return null;
        }
    }

    console.debug('matchRoute params:', params);
    return params;
}

/**
 * Initialize the router with route definitions and an optional guard.
 */
export function initRouter(routeMap, guard = null) {
    routes = routeMap;
    routeGuard = guard;

    window.addEventListener('hashchange', handleRoute);
    handleRoute();
}

/**
 * Navigate to a given path (updates the URL hash).
 */
export function navigate(path) {
    window.location.hash = path;
}

/**
 * Get the current path from the hash (without the leading '#').
 */
function getCurrentPath() {
    const hash = window.location.hash;
    return hash ? hash.slice(1) : '/';
}

/**
 * Handle a route change: apply guard, find matching route, render with params.
 */
function handleRoute() {
    const path = getCurrentPath();

    // Run guard if provided and path is protected
    if (routeGuard && !routeGuard(path)) {
        return;
    }

    currentPath = path;

    // Find matching route (exact or pattern)
    for (const [pattern, renderFn] of Object.entries(routes)) {
        const params = matchRoute(pattern, path);
        if (params !== null && typeof params === 'object') {
            // Pass params to the render function
            renderFn(params);
            return;
        }
    }

    // Fallback: 404
    document.getElementById('app').innerHTML = `<h1>404 — Page not found</h1>`;
}