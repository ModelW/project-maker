/**
 * Session provider backed by the API's "me" endpoints, through the generated
 * API client (see `$lib/api`).
 */

import { createApiClient } from "$lib/api";
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

/** Session provider talking to the API */
export const sessionProvider: SessionProvider = {
    fetchMe: (fetch) => createApiClient(fetch).me.whoami(),
    login: (fetch, credentials) => createApiClient(fetch).me.login(credentials),
    logout: (fetch) => createApiClient(fetch).me.logout(),
};
