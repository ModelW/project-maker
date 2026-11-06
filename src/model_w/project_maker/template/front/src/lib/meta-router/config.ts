/**
 * Configuration of the meta router: which routes need the visitor to be
 * logged in, which ones need a fresh session and where to send anonymous
 * visitors. This is the file to edit.
 *
 * Rules are applied by the root layout's load function on every navigation
 * (server-side on the first page load, then in the browser). The session is
 * only fetched when a matched rule needs it, so public pages cost no extra
 * request.
 *
 * Keep in mind that this is about user experience, not security: the API
 * must check permissions on its own, as it already does.
 */

import { browser } from "$app/env";
import { sessionProvider } from "$lib/session/provider";
import {
    createMemorySessionCache,
    createMetaRouter,
    noopSessionCache,
    type RouteRule,
} from "./router";

/**
 * Where anonymous visitors get sent when they try to reach a route which
 * requires authentication. Change it here (and only here) when the project
 * gets its own login page.
 *
 * @param next The URL the visitor wanted to reach, to come back to it after
 *             logging in
 */
export function loginUrl(next: URL): string {
    const nextParam = encodeURIComponent(`${next.pathname}${next.search}`);

    // :: IF api__wagtail
    return `/back/___admin_prefix___/cms/login/?next=${nextParam}`;
    // :: ENDIF
    // :: IF api__enable
    // :: IFNOT api__wagtail
    return `/back/___admin_prefix___/admin/login/?next=${nextParam}`;
    // :: ENDIF
    // :: ENDIF
    // :: IFNOT api__enable
    return `/login/?next=${nextParam}`;
    // :: ENDIF
}

/**
 * Rules applied to the URLs, first match wins. URLs that match no rule are
 * public and don't touch the session.
 *
 * - `requiresAuth`: anonymous visitors are redirected to `loginUrl()`
 * - `refreshSession`: the session is fetched again on each navigation there
 *
 * @example
 * ```ts
 * { match: /^\/account(\/|$)/, requiresAuth: true, refreshSession: true }
 * ```
 */
export const routeRules: RouteRule[] = [
    // :: IF api__wagtail
    // Previews are rendered by the front but only make sense for editors
    { match: (url) => url.searchParams.has("in_preview_panel"), requiresAuth: true },
    { match: /^\/__block_preview__\/?$/, requiresAuth: true },
    { match: /^\/__snippet_preview__\/?$/, requiresAuth: true },
    // :: ENDIF
];

/**
 * The meta router used by the app. The session is remembered in memory in
 * the browser, but never on the server where it would be shared between
 * visitors.
 */
export const metaRouter = createMetaRouter({
    rules: routeRules,
    loginUrl,
    sessionProvider,
    cache: browser ? createMemorySessionCache() : noopSessionCache,
});
