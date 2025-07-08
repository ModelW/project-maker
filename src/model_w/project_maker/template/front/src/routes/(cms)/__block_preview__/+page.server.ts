/**
 * Server side load function for the CMS block preview route.
 * It fetches the block data from the Wagtail API and returns it to the universal load
 * function to render the correct block component.
 */

import type { PageServerLoad } from "./$types";
import { fetchBlockData } from "$lib/utils/cms";

/** Server side load function for the block preview route. */
export const load: PageServerLoad = async ({ fetch, url }) => {
    /** The block ID being previewed. */
    const blockId = url.searchParams.get("id") ?? "";
    /** The app dot model of the block being previewed. */
    const inPreviewPanel = url.searchParams.get("in_preview_panel") ?? "";
    /** The block data being previewed. */
    const blockData = await fetchBlockData(fetch, blockId, inPreviewPanel);
    return {
        blockData,
    };
};
