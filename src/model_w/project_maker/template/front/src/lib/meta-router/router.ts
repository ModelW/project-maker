/**
 * The meta router decides, for each navigation, whether the visitor's session
 * must be known (and fetched) and whether the visitor is allowed in.
 *
 * It knows nothing about the API, the login page or the environment: all of
 * that is injected by `./config.ts`, which is the file to edit.
 */

import { redirect } from "@sveltejs/kit";
import type { SessionProvider } from "$lib/session/provider";
import type { Me } from "$lib/session/types";

/** Describes how to treat a group of routes */
export interface RouteRule {
    /**
     * Which URLs the rule applies to. A regular expression is tested against
     * the pathname, a function receives the full URL (to look at the query
     * string for example).
     */
    match: RegExp | ((url: URL) => boolean);

    /**
     * Anonymous visitors get redirected to the login URL. The session is only
     * fetched if it is not already known to be authenticated.
     */
    requiresAuth?: boolean;

    /** The session is fetched again each time the visitor navigates there */
    refreshSession?: boolean;
}

/**
 * Remembers the session between navigations, so that it's not fetched again
 * for each protected page.
 */
export interface SessionCache {
    /** The last known session, if any */
    get(): Me | null;

    /** Stores a freshly fetched session */
    set(me: Me): void;

    /** Marks the session as stale: the next resolution will fetch it again */
    requestRefresh(): void;

    /** Returns true (once) if a refresh has been requested */
    consumeRefresh(): boolean;
}

/** Everything the meta router depends on */
export interface MetaRouterDeps {
    /** Rules, first match wins. URLs without a match are public. */
    rules: RouteRule[];

    /** Where the session comes from */
    sessionProvider: SessionProvider;

    /** Builds the URL to send anonymous visitors to */
    loginUrl: (next: URL) => string;

    /** Where the session is remembered */
    cache: SessionCache;
}

/** Arguments of a resolution, as given by a SvelteKit load function */
export interface ResolveArgs {
    url: URL;
    fetch: typeof globalThis.fetch;
}

/**
 * The outcome of a resolution. `me` is `null` when nobody needed the session
 * for this navigation: it means "unknown", not "anonymous".
 */
export interface Resolution {
    me: Me | null;
}

/** Session cache living in memory, for the browser */
export function createMemorySessionCache(): SessionCache {
    let me: Me | null = null;
    let stale = false;

    return {
        get: () => me,
        set: (value) => {
            me = value;
        },
        requestRefresh: () => {
            stale = true;
        },
        consumeRefresh: () => {
            const out = stale;
            stale = false;
            return out;
        },
    };
}

/**
 * Session cache that never remembers anything. Used on the server, where a
 * cache would be shared between all visitors.
 */
export const noopSessionCache: SessionCache = {
    get: () => null,
    set: () => undefined,
    requestRefresh: () => undefined,
    consumeRefresh: () => false,
};

function matches(rule: RouteRule, url: URL): boolean {
    return rule.match instanceof RegExp ? rule.match.test(url.pathname) : rule.match(url);
}

/**
 * Creates the meta router.
 *
 * @param deps Rules and services the router relies on
 */
export function createMetaRouter(deps: MetaRouterDeps) {
    return {
        deps,

        /**
         * Applies the rules to a navigation. Fetches the session only when
         * the matched rule (or an explicit refresh) requires it, and
         * redirects anonymous visitors away from protected routes.
         *
         * @param args The URL being navigated to and SvelteKit's fetch
         */
        async resolve({ url, fetch }: ResolveArgs): Promise<Resolution> {
            const rule = deps.rules.find((r) => matches(r, url));
            const cached = deps.cache.get();
            const mustFetch =
                deps.cache.consumeRefresh() ||
                !!rule?.refreshSession ||
                (!!rule?.requiresAuth && cached?.type !== "authenticated");

            let me = cached;

            if (mustFetch) {
                me = await deps.sessionProvider.fetchMe(fetch);
                deps.cache.set(me);
            }

            if (rule?.requiresAuth && me?.type !== "authenticated") {
                redirect(307, deps.loginUrl(url));
            }

            return { me };
        },
    };
}

/** The meta router, as created by `createMetaRouter()` */
export type MetaRouter = ReturnType<typeof createMetaRouter>;
