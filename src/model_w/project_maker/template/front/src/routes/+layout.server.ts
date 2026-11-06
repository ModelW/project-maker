/**
 * Root server load: data shared by every page.
 *
 * This runs on the server only, and only once per visit: it depends on
 * neither the URL nor the params, so SvelteKit doesn't call it again on
 * client-side navigations.
 */

import { getMenus } from "$lib/navigation/menus";
import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = async ({ fetch }) => {
    return {
        menus: await getMenus(fetch),
    };
};
