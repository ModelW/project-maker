/**
 * Utility functions for fetch operations.
 */

import { error, isHttpError } from "@sveltejs/kit";

/**
 * Wraps a fectch promise and raises the appropriate HTTP errors according to what is received.
 *
 * @param {Promise<Response>} fetchPromise - A promise that resolves to a Response object, typically from calling `fetch`.
 * @returns {Promise<any>} - The JSON-parsed response body if the request is successful.
 */
export async function fetchWithErrorHandling(fetchPromise: Promise<Response>): Promise<any> {
    try {
        const response = await fetchPromise;
        const pageData = await response.json();

        if (!response.ok) {
            error(response.status, pageData);
        }

        return pageData;
    } catch (e) {
        // Pass on API HTTP status errors
        if (isHttpError(e)) {
            error(e.status, e.body); // User seen error message
        }
        console.error(e); // Detailed server error logging
        error(500, "Internal server error"); // User seen error message
    }
}
