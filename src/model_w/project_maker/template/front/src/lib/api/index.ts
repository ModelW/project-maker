/**
 * Client of the API. This is the only way the front should talk to the API.
 *
 * The `client/` directory is generated from the Django Ninja OpenAPI schema:
 * never edit it by hand, run `make ts_client` in the `api/` directory instead
 * (whenever an endpoint or a schema changes) and commit the result.
 *
 * URLs are relative (`/back/api/...`): the API and the front share the same
 * origin. In the browser the load balancer (or Vite's proxy in development)
 * routes `/back/` to the API, and on the server `handleFetch` (see
 * `hooks.server.ts`) forwards those requests to `API_URL`, with the visitor's
 * cookies.
 */

import { Configuration, MeApi } from "./client";

export type { AnonUserOut, AuthUserIn, AuthUserOut, Me } from "./client";

/** All the endpoints of the API, grouped like the routers of Ninja */
export interface ApiClient {
    /** The /back/api/me endpoints (whoami, login, logout) */
    me: MeApi;
}

/**
 * Creates the API client.
 *
 * @param fetch The fetch to use: SvelteKit's in load functions (so that
 *              SSR requests are forwarded with cookies and responses reused
 *              when hydrating), the global one elsewhere
 */
export function createApiClient(fetch: typeof globalThis.fetch): ApiClient {
    const configuration = new Configuration({ basePath: "", fetchApi: fetch });

    return {
        me: new MeApi(configuration),
    };
}
