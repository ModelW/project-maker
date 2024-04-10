import { type FetchResponse } from "ofetch";
import { useLayoutStore } from "@/stores/layout";
import { type NuxtError } from "#app";

const isBrowser = typeof window !== "undefined";
const isServer = !isBrowser;

const REDIRECT_CODE = [301, 302, 307, 308];

/**
 * The fetching of data for the wagtail page is done in this middleware. This
 * allows to ensure that the whole data fetching happens *before* the
 * navigation, hence making sure that the HTML code of the page is fully
 * available from any part may it be the page itself or the layout.
 *
 * Also Nuxt looks less pissy about interrupting navigation and stuff like that
 * when done from the middleware so yay?
 */
export default defineNuxtRouteMiddleware(async (to) => {
    /**
     * Just the raw HTTP query to get the response from Django. If we're on the
     * server, we're adding the appropriate headers so that the authentication
     * and other security measures can be passed along (which allows for
     * previews to work).
     */
    async function fetchDjangoPage(): Promise<FetchResponse<string>> {
        const headers: Record<string, string> = {
            "X-Reach-API": "yes",
        };

        if (isServer) {
            const proxyHeaders = useRequestHeaders([
                "cookie",
                "origin",
                "referrer",
                "x-csrftoken",
            ]);
            Object.assign(headers, proxyHeaders);

            const hostCandidates = useRequestHeaders([
                "host",
                "x-forwarded-host",
            ]);
            const host =
                hostCandidates["x-forwarded-host"] || hostCandidates["host"];

            if (host) {
                headers["X-Forwarded-Host"] = host;
            }
        }

        /**
         * After this middleware was added, NuxtLinks stopped working
         * due to missing the trailing slashes always needed by wagtail,
         * so we check if a link needs a trailing slash or not here
         */
        let url = to.fullPath;
        if (!url.endsWith("/")) {
            url += "/";
        }

        return await $fetch.raw(url, {
            baseURL: isBrowser ? undefined : useNuxtApp().$config.apiUrl,
            headers,
            redirect: "manual",
            params: { x: "" },
        });
    }

    /**
     * When we receive a redirect status from Wagtail, we throw an error with data.location
     * to know where to `navigateTo()`.
     */
    interface WagtailRedirectData {
        location: string;
    }

    /** The error type expected when a redirect status is returned from the server */
    interface WagtailRedirect extends NuxtError {
        data: WagtailRedirectData;
    }

    /**
     * Depending on the response, we'll either return the HTML to be used to
     * render the page or throw an error:
     *
     * - If it's a redirect, the error will have the status code of the redirect
     *   and contain a location in the data field. The goal is that the setup
     *   function can then navigate to that location.
     * - Otherwise it's any kind of error, and we'll re-throw it from the setup
     *   function so that the error page is triggered.
     */
    function decideResponseStrategy(resp: FetchResponse<string>) {
        if (200 <= resp.status && resp.status < 300) {
            const html = resp._data;

            if (html) {
                return {
                    html,
                };
            } else {
                throw createError({
                    statusCode: 500,
                    message: "Empty response",
                });
            }
        } else if (REDIRECT_CODE.includes(resp.status)) {
            const location = resp.headers.get("location");

            if (location) {
                throw createError<WagtailRedirectData>({
                    statusCode: resp.status,
                    message: "Redirect",
                    data: { location },
                });
            } else {
                throw createError({
                    statusCode: 500,
                    message: "Invalid redirect",
                });
            }
        } else {
            throw createError({
                statusCode: resp.status,
                message: resp.statusText,
            });
        }
    }

    /**
     * This is in charge of getting the HTML from the server.
     *
     * Basically we're expecting a 200 status code. If that's the case, the
     * content should be HTML and we'll work with that.
     *
     * If not we try to figure out what is going on. If we've got a redirection
     * then we translate the redirection into Nuxt. Otherwise we just forward
     * the error. It's up to the implementer to handle errors 404, 500, etc.
     *
     * Let's note that those actions will be decided inside here but the action
     * will be taken from the setup function because Nuxt is made in a very
     * logical way apparently.
     *
     * Let's note that this works slightly different depending on if we're
     * running on the server side or the client side. Indeed, on the server
     * you'll have a `$config.apiUrl` value which allows to hit directly the
     * internal API URL, while on the client this value will be undefined and
     * we'll hit the URL relatively to the root path using the `x-reach-api`
     * header to tell the proxy to get this page from the API for us.
     */
    async function getServerData() {
        const resp = await fetchDjangoPage();
        const data = decideResponseStrategy(resp);
        return data;
    }

    try {
        const data = await getServerData();

        if (
            typeof data === "object" &&
            data !== null &&
            "html" in data &&
            typeof data.html === "string"
        ) {
            const htmlTemplate = data.html;
            useLayoutStore().setPageHtml(htmlTemplate);
        }
    } catch (fetchError) {
        const error = fetchError as any as Error | NuxtError;

        if ("statusCode" in error && REDIRECT_CODE.includes(error.statusCode)) {
            return navigateTo((error as WagtailRedirect).data.location, {
                redirectCode: error.statusCode,
            });
        } else {
            return abortNavigation(error);
        }
    }
});
