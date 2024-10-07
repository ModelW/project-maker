import { sequence } from "@sveltejs/kit/hooks";
import * as Sentry from "@sentry/sveltekit";
import { env } from "$env/dynamic/private";
import { env as publicEnv } from "$env/dynamic/public";
import type { HandleFetch } from "@sveltejs/kit";

Sentry.init({
    dsn: publicEnv.PUBLIC_SENTRY_DSN,
    environment: publicEnv.PUBLIC_SENTRY_ENVIRONMENT,
    tracesSampleRate: 1,
});

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
 * URL is only known through private environment variables, which are not disclosed to
 * client-side. However since the API client's code is accessible both from the client
 * and server side, it cannot import environment variables. The solution to this is that
 * convention of using http://api as an origin if you're trying to reach out the API and
 * you are on the server side.
 *
 * Other requests are left untouched.
 */
export const handleFetch: HandleFetch = async function handleFetch({ event, request, fetch }) {
    const internalApiOrigin = "http://api";
    const url = new URL(request.url, internalApiOrigin);
    const apiUrl = new URL(env.API_URL);
    const isApiQuery = url.origin === internalApiOrigin;

    if (isApiQuery) {
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

export const handleError = Sentry.handleErrorWithSentry();

export const handle = sequence(Sentry.sentryHandle());
