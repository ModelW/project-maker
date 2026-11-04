/**
 * Server side load function for the CMS snippet preview route.
 * It fetches the snippet data from the Wagtail API and returns it to the universal
 * load function to render the correct snippet component.
 */

import type { PageType } from "$lib/components/cms/pages/types";
import { fetchSnippetData } from "$lib/utils/cms";
import type { PageServerLoad } from "./$types";

/** Server side load function for the snippet preview route. */
export const load: PageServerLoad = async ({ fetch, url }) => {
    /** The app dot model of the snippet being previewed (e.g. cms.DemoSnippet) */
    const snippetType = url.searchParams.get("in_preview_panel") ?? "";
    /** The ID of the snippet being previewed, if it exists already */
    const snippetId = url.searchParams.get("id");
    /** The snippet data being previewed (read from the session by the backend). */
    const snippetData = (await fetchSnippetData(fetch, snippetType, snippetId)) as PageType;

    return {
        snippetData,
    };
};
