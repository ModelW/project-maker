/**
 * Server side load function for the dynamic catch-all CMS page route.
 * It fetches the page data from the Wagtail API and returns it to the universal load
 * function to render the correct page component.
 */

import type { PageServerLoad } from "./$types";
import { fetchCmsData } from "$lib/utils/cms";

/** Server side load function for the dynamic page route. */
export const load: PageServerLoad = async ({ fetch, params, url }) => {
    /** The CMS page data (or preview data if `in_preview_panel` query param). */
    const pageData = await fetchCmsData(
        fetch,
        params.cmsPath,
        url.searchParams.get("in_preview_panel")
    );

    return {
        pageData,
    };
};
