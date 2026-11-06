/**
 * Keeps the CMS catch-all route away from `/back/`, which belongs to the API.
 *
 * Without it, client-side navigations to `/back/...` (links to the admin,
 * redirections to the login page) would be handled by the CMS route and end
 * up in a 404. With it, no route matches and SvelteKit lets the browser load
 * the page normally.
 */

import type { ParamMatcher } from "@sveltejs/kit";

export const match: ParamMatcher = (param) => !/^back(\/|$)/.test(param);
