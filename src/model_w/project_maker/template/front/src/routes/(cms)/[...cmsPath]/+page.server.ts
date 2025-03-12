/**
 * Server side load function for the dynamic catch-all CMS page route.
 * It fetches the page data from the Wagtail API and returns it to the universal load
 * function to render the correct page component.
 */

import type { PageServerLoad } from "./$types";
import type { PageType } from "$lib/components/cms/pages/types";
import { fetchCmsData, fetchUserbar } from "$lib/utils/cms";

/** Keep trailing slash consistent with Wagtail/Django URLs. */
export const trailingSlash = "always";

/** Server side load function for the dynamic page route. */
export const load: PageServerLoad = async ({ fetch, params, url }) => {
    const inPreviewPanel = url.searchParams.get("in_preview_panel");

    /** The CMS page data (or preview data if `in_preview_panel` query param). */
    const pageData: PageType = await fetchCmsData(fetch, params.cmsPath, inPreviewPanel);

    const userbar = await fetchUserbar(fetch, pageData.id, inPreviewPanel);

    return {
        pageData,
        userbar,
    };
};
