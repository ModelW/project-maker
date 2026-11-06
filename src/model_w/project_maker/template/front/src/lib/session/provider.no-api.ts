/**
 * Session provider for projects without the Model W API. Replaces
 * `provider.ts` at generation time.
 *
 * Nothing calls it as long as no route rule needs the session (see
 * `$lib/meta-router/config.ts`). Implement it against your own
 * authentication backend if you need one.
 */

import type { Credentials, Me } from "./types";

/** Contract of whatever knows who the visitor is. */
export interface SessionProvider {
    /** Retrieves the current session */
    fetchMe(fetch: typeof globalThis.fetch): Promise<Me>;

    /** Logs in and returns the resulting session */
    login(fetch: typeof globalThis.fetch, credentials: Credentials): Promise<Me>;

    /** Logs out and returns the resulting (anonymous) session */
    logout(fetch: typeof globalThis.fetch): Promise<Me>;
}

function notImplemented(): Promise<never> {
    return Promise.reject(
        new Error("No session backend: implement one in $lib/session/provider.ts")
    );
}

/** Placeholder session provider */
export const sessionProvider: SessionProvider = {
    fetchMe: notImplemented,
    login: notImplemented,
    logout: notImplemented,
};
