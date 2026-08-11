/**
 * Format API error responses into a human-readable string.
 *
 * Supports two shapes:
 * - { error: "Invalid email or password" }            (login)
 * - { error: { title: ["Missing data"], ... } }        (submission, admin)
 */
export function formatApiError(errorData) {
    if (!errorData) return 'An unknown error occurred.';

    // If it's a string, return it directly
    if (typeof errorData === 'string') {
        return errorData;
    }

    // If it's an object with a top-level 'error' that is a string
    if (errorData.error && typeof errorData.error === 'string') {
        return errorData.error;
    }

    // If it's an object with nested field errors
    if (typeof errorData === 'object' && !Array.isArray(errorData)) {
        const messages = [];
        for (const [field, errors] of Object.entries(errorData)) {
            if (field === 'error') continue; // already handled above
            if (Array.isArray(errors)) {
                messages.push(`${field}: ${errors.join(', ')}`);
            } else if (typeof errors === 'string') {
                messages.push(`${field}: ${errors}`);
            }
        }
        if (messages.length > 0) {
            return messages.join('; ');
        }
        // Fallback: stringify the whole object
        return JSON.stringify(errorData);
    }

    return String(errorData);
}