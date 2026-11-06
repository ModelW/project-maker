// Sentry gets initialized in instrumentation.server.ts, before any app code
import { sequence } from "@sveltejs/kit/hooks";
// :: IF api__enable
import type { HandleFetch } from "@sveltejs/kit";
// :: ENDIF
import type { Handle, HandleServerError } from "@sveltejs/kit";
import * as Sentry from "@sentry/sveltekit";
// :: IF api__enable
import { API_URL } from "$app/env/private";
// :: ENDIF
import { accessLog } from "$lib/utils/access_log";

// :: IF api__enable
/**
 * The things you might want to change in a request
 */
interface RequestPatch {
    /**
     * New URL to be given
     */
    url?: string | URL;

    /**
     * New headers to be appended (not replaced)
     */
    appendHeaders?: Headers;

    /**
     * Request mode (in case you want to avoid CORS)
     */
    mode?: RequestMode;
}

/**
 * Convenience function to copy and patch a request object in a way that works
 *
 * @param request Initial request received from the hook
 * @param patch Things you want to change about this request
 */
async function patchRequest(request: Request, patch: RequestPatch): Promise<Request> {
    const headers = new Headers(request.headers);

    if (patch.appendHeaders) {
        patch.appendHeaders.forEach((value, key) => {
            headers.append(key, value);
        });
    }

    const url = patch.url !== undefined ? patch.url : request.url;
    const mode = patch.mode !== undefined ? patch.mode : request.mode;
    const body = request.method !== "GET" ? await request.text() : undefined;

    const init = {
        method: request.method,
        headers,
        body,
        mode,
        cache: request.cache,
        credentials: request.credentials,
        destination: request.destination,
        integrity: request.integrity,
        redirect: request.redirect,
        referrer: request.referrer,
        referrerPolicy: request.referrerPolicy,
        signal: request.signal,
    };

    return new Request(url, init);
}

/**
 * We have an internal convention that is that if the origin of a request is http://api
 * we consider that the request is to be made to the API server and thus modify the
 * request in-situ to hit the actual API server.
 *
 * This hook only runs on the server-side and works like that because the API internal
 * URL is only known through a private environment variable (API_URL), which are not disclosed to
 * client-side. However since the API client's code is accessible both from the client
 * and server side, it cannot import environment variables. The solution to this is that
 * convention of using http://api as an origin if you're trying to reach out the API and
 * you are on the server side.
 *
 * Same-origin requests to `/back/` get the same treatment: in production the router
 * sends them to the API, so on the server side we do the same. This allows code
 * running on both sides to simply use relative `/back/...` URLs.
 *
 * Other requests are left untouched.
 */
export const handleFetch: HandleFetch = async function handleFetch({ event, request, fetch }) {
    const internalApiOrigin = "http://api";
    const url = new URL(request.url, internalApiOrigin);
    const isApiQuery =
        url.origin === internalApiOrigin ||
        (url.origin === event.url.origin && url.pathname.startsWith("/back/"));

    if (isApiQuery) {
        const apiUrl = new URL(API_URL);
        const extraHeaders = new Headers();
        const cookie = event.request.headers.get("cookie");
        if (cookie) {
            extraHeaders.append("Cookie", cookie);
        }

        request = await patchRequest(request, {
            url: `${apiUrl.origin}${url.pathname}${url.search}`,
            appendHeaders: extraHeaders,
            mode: "cors",
        });
    }

    return fetch(request);
};
// :: ENDIF

/** Log error in server console as well as sending to Sentry. */
const errorHandler: HandleServerError = ({ error, event }) => {
    console.error("Server side error:", error, event);
};

export const handleError = Sentry.handleErrorWithSentry(errorHandler);

/**
 * Allows in-browser JS profiling, which Sentry's browser profiling needs.
 *
 * See https://docs.sentry.io/platforms/javascript/guides/sveltekit/profiling/browser-profiling/
 */
const documentPolicy: Handle = async ({ event, resolve }) => {
    const response = await resolve(event);

    if (response.headers.get("content-type")?.includes("text/html")) {
        response.headers.set("Document-Policy", "js-profiling");
    }

    return response;
};

export const handle = sequence(documentPolicy, Sentry.sentryHandle(), accessLog);
