/**
 * Utility functions for fetch operations.
 */

import { captureException } from "@sentry/sveltekit";
import { error, isHttpError, isRedirect, redirect } from "@sveltejs/kit";
/**
 * Wraps a fetch promise and raises the appropriate HTTP errors according to what is received.
 *
 * @param {Promise<Response>} fetchPromise - A promise that resolves to a Response object, typically from calling `fetch`.
 * @returns {Promise<any>} - The JSON-parsed response body if the request is successful.
 */
export async function fetchWithErrorHandling(fetchPromise: Promise<Response>): Promise<any> {
    try {
        const response = await fetchPromise;
        const redirectUrl = response.headers.get("X-Redirect-To");

        if (response.ok) {
            const pageData = await response.json();
            return pageData;
        }

        if (300 <= response.status && response.status <= 308) {
            const location = redirectUrl || response.headers.get("location");
            if (location) {
                return redirect(response.status, location);
            } else {
                throw Error(`No location found for redirect ${response.status}.`);
            }
        }

        error(response.status);
    } catch (e) {
        captureException(e);

        if (isHttpError(e)) {
            error(e.status, e.body);
        }
        if (isRedirect(e)) {
            redirect(e.status, e.location);
        }

        error(500, "Internal server error");
    }
}
