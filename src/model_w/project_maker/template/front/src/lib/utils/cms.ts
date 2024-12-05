/**
 * Utility functions for working with the CMS.
 */

import type { ComponentType } from "svelte";
import { fetchWithErrorHandling } from "$lib/utils/fetchUtils";

/**
 * To have a block know how to render itself just from its own type (matching to a Svelte Component in blocks/),
 * and have SSR work, the server imports all block components and makes them available at $page.blockComponents.
 * Then they can be rendered as follows:
 * ```svelte
 *  {#each cmsData.blocks as block}
 *      <svelte:component this={$page.data.blockComponents[block.type]} cmsData={block.value} />
 *  {/each}
 * ```
 *
 * Performance:  Initial SSR page load is super fast.  Then hydration takes a while.  Once hydrated all
 *               blocks are available for all components and all is fast.
 *
 * The shape of the returned object is:
 * { 'DemoBlock': <DemoBlock /> }
 */
export async function getBlockComponents() {
    const blockComponents: Record<string, ComponentType> = {};

    /**
     * Import all svelte components in the blocks folder with import.meta.glob wildcard.
     *
     * The shape of the blockImports object is:
     * { '/src/lib/components/cms/blocks/DemoBlock.svelte': () => import('./DemoBlock.svelte').default }
     */
    const blockImports = import.meta.glob("$lib/components/cms/blocks/*.svelte", {
        import: "default",
    }) as Record<string, () => Promise<ComponentType>>;

    // Import the block components and store in blockComponents object
    for (const blockImport in blockImports) {
        const filePathSplit = blockImport.split("/");
        const block_type = filePathSplit[filePathSplit.length - 1].replace(".svelte", "");
        blockComponents[block_type] = await blockImports[blockImport]();
    }

    return blockComponents;
}

/**
 * Constructs the URL for the CMS based on whether the page is in preview mode.
 * @param {string} cmsPath - The parameter from the URL to define API path.
 * @param {string | null} previewmodel - If the page is in preview mode, this will be passed.
 * @returns {URL} - The constructed URL for the CMS API.
 */
function constructCmsUrl(cmsPath: string, previewmodel: string | null): URL {
    const baseUrl = "http://api/back/api/cms/";
    return new URL(
        previewmodel
            ? `${baseUrl}preview/?preview_model=${previewmodel}`
            : `${baseUrl}pages/find/?html_path=${cmsPath}&fields=*`
    );
}

/**
 * Fetch CMS data for a page based on the constructed URL.
 * @param {Function} fetch - The fetch function provided by SvelteKit.
 * @param {string} cmsPath - The CMS HTML path.
 * @param {string | null} previewPage - Indicates if the page is in preview mode.
 * @returns {Promise<any>} - The fetched page data.
 */
export async function fetchCmsData(
    fetch: typeof globalThis.fetch,
    cmsPath: string,
    previewPage: string | null
): Promise<any> {
    const cmsUrl = constructCmsUrl(cmsPath, previewPage);
    return await fetchWithErrorHandling(fetch(cmsUrl));
}
