/**
 * Root universal load: applies the meta router's rules (see
 * `$lib/meta-router/config.ts`) on every navigation.
 *
 * It runs on the server for the first page and in the browser afterwards,
 * which is what allows protecting client-side navigations too. Thanks to the
 * session cache and to the rules, it only hits the API when needed.
 */

import { metaRouter } from "$lib/meta-router/config";
import { SESSION_DEPENDENCY } from "$lib/session/context";
import type { LayoutLoad } from "./$types";

export const load: LayoutLoad = async ({ data, url, fetch, depends }) => {
    depends(SESSION_DEPENDENCY);

    const { me } = await metaRouter.resolve({ url, fetch });

    return {
        ...data,
        me,
    };
};
