/**
 * Makes the visitor's session available to any component, along with the
 * actions that change it.
 */

import { invalidate } from "$app/navigation";
import { createContext } from "svelte";
import type { MetaRouterDeps } from "$lib/meta-router/router";
import type { Credentials, Me } from "./types";

/** Dependency key used by the root layout's load, to re-run it on demand */
export const SESSION_DEPENDENCY = "app:session";

/** What `useSession()` gives access to */
export interface SessionHandle {
    /**
     * The visitor's session, or `null` if it is unknown because no rule of
     * the meta router needed it for the current page. Call `refresh()` if
     * the component needs to know in any case.
     */
    readonly me: Me | null;

    /** Shortcut to know if the visitor is logged in (`null` if unknown) */
    readonly isAuthenticated: boolean | null;

    /** Fetches the session again */
    refresh(): Promise<void>;

    /** Logs in through the session provider */
    login(credentials: Credentials): Promise<Me>;

    /** Logs out through the session provider */
    logout(): Promise<Me>;
}

const [getSession, setSession] = createContext<SessionHandle>();

/**
 * Creates the session handle and registers it for the whole component tree.
 * Called once by the root layout.
 *
 * Every action goes through the meta router's cache then invalidates the
 * root layout's load, so that the page data (and the rules, which might now
 * redirect) follow the new session.
 *
 * @param me Getter returning the session from the page data
 * @param deps The meta router's dependencies
 */
export function provideSession(
    me: () => Me | null,
    deps: Pick<MetaRouterDeps, "sessionProvider" | "cache">
): void {
    const { sessionProvider, cache } = deps;

    async function update(newMe: Me): Promise<Me> {
        cache.set(newMe);
        await invalidate(SESSION_DEPENDENCY);
        return newMe;
    }

    setSession({
        get me() {
            return me();
        },
        get isAuthenticated() {
            const current = me();
            return current ? current.type === "authenticated" : null;
        },
        async refresh() {
            cache.requestRefresh();
            await invalidate(SESSION_DEPENDENCY);
        },
        async login(credentials) {
            return update(await sessionProvider.login(fetch, credentials));
        },
        async logout() {
            return update(await sessionProvider.logout(fetch));
        },
    });
}

/**
 * Gives access to the visitor's session from anywhere in the app.
 *
 * Like any Svelte context, this must be called during the component's
 * initialisation (at the top level of its `<script>`). The returned object
 * is reactive.
 *
 * @example
 * ```svelte
 * <script lang="ts">
 *     const session = useSession();
 * </script>
 *
 * {#if session.me?.type === "authenticated"}
 *     Hello {session.me.firstName}
 * {/if}
 * ```
 */
export function useSession(): SessionHandle {
    return getSession();
}
