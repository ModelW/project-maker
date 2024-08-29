/**
 * Server side load function for the dynamic catch-all Wagtail page route.
 * It fetches the page data from the Wagtail API and returns it to the universal load
 * function to render the correct page component.
 */

import type { PageServerLoad } from "./$types";
import { fetchWithErrorHandling } from "$lib/utils/fetchUtils";

/**
 * This function is the server side load function for the dynamic page route.
 */
export const load: PageServerLoad =
    /**
     * This function fetches the page data from the Wagtail API and returns it to the client.
     * Note: We could be in preview mode, if "in_preview_panel" is a query parameter.
     *       In this case, we get the data from the cms preview endpoint.
     */
    async ({ fetch, params, url }) => {
        const previewPage = url.searchParams.get("in_preview_panel");

        const wagtailPageUrl = previewPage
            ? new URL(`http://api/back/api/cms/preview/?preview_model=${previewPage}`)
            : new URL(`http://api/back/api/cms/pages/find/?html_path=${params.wagtail}&fields=*`);

        const pageData = await fetchWithErrorHandling(fetch(wagtailPageUrl));

        return {
            pageData,
        };
    };
