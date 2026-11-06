/**
 * Utility functions for working with the CMS.
 */

import type { Component } from "svelte";
import type { WagtailUserbarType } from "$lib/components/cms/pages/types";
import { fetchWithErrorHandling } from "$lib/utils/fetchUtils";
import { captureException, captureMessage } from "@sentry/sveltekit";

const API_CMS_BASE_URL = "http://api/back/api/cms/";

/** A StreamField block, as serialized by the API */
export interface StreamFieldBlock<T = unknown> {
    /** Name of the block, matching a component in `$lib/components/cms/blocks/` */
    type: string;

    /** Content of the block, given to the component as `cmsData` */
    value: T;

    /** Unique ID of the block within the StreamField */
    id?: string;
}

/** Block components by block type, as returned by `getBlockComponents()` */
export type BlockComponents = Record<string, Component<any>>;

/**
 * Checks if a value looks like a StreamField block
 *
 * @param value Any value from the API
 */
function isBlock(value: unknown): value is StreamFieldBlock {
    return (
        typeof value === "object" &&
        value !== null &&
        "type" in value &&
        "value" in value &&
        typeof value.type === "string"
    );
}

/**
 * Lists the types of all the StreamField blocks found in some API data, at
 * any depth (so blocks nested in blocks are found as well).
 *
 * @param data Data from the API (a page, a block, a snippet...)
 * @returns The block types, without duplicates
 */
export function collectBlockTypes(data: unknown): string[] {
    const types = new Set<string>();

    function walk(value: unknown): void {
        if (Array.isArray(value)) {
            value.forEach(walk);
        } else if (typeof value === "object" && value !== null) {
            if (isBlock(value)) {
                types.add(value.type);
            }

            Object.values(value).forEach(walk);
        }
    }

    walk(data);

    return [...types];
}

/**
 * This is the registry that maps StreamField blocks to their components: a
 * block of type `Foo` is rendered by `$lib/components/cms/blocks/Foo.svelte`.
 * There is nothing to register by hand, adding the file is enough.
 *
 * The universal load functions of the CMS routes call it with the block
 * types found in the data, so that SSR has all the components it needs, and
 * expose the result as `blockComponents` in the page data. Then the
 * `StreamField` component renders the blocks:
 *
 * ```svelte
 * <StreamField blocks={cmsData.body} />
 * ```
 *
 * Each block is a separate code-split chunk, only the blocks listed in
 * `neededTypes` are actually loaded.
 *
 * @param neededTypes Block types to load (all of them if not specified)
 * @returns The components, by block type (e.g. `{ DemoBlock: DemoBlock }`)
 */
export async function getBlockComponents(
    neededTypes?: string[]
): Promise<BlockComponents> {
    const blockComponents: BlockComponents = {};

    /**
     * The shape of the blockImports object is:
     * { '/src/lib/components/cms/blocks/DemoBlock.svelte': () => import('./DemoBlock.svelte') }
     */
    const blockImports = import.meta.glob("$lib/components/cms/blocks/*.svelte", {
        import: "default",
    }) as Record<string, () => Promise<Component<any>>>;

    const typeToPath: Record<string, string> = {};

    for (const filePath in blockImports) {
        const blockType = filePath.split("/").pop()!.replace(".svelte", "");
        typeToPath[blockType] = filePath;
    }

    const typesToLoad =
        neededTypes !== undefined
            ? neededTypes.filter((t) => t in typeToPath)
            : Object.keys(typeToPath);

    await Promise.all(
        typesToLoad.map(async (blockType) => {
            blockComponents[blockType] = await blockImports[typeToPath[blockType]]();
        })
    );

    return blockComponents;
}

/**
 * Constructs the URL for the CMS based on whether the page is in preview mode.
 * @param {string} cmsPath - The parameter from the URL to define API path.
 * @param {string | null} previewmodel - If the page is in preview mode, this will be passed.
 * @returns {URL} - The constructed URL for the CMS API.
 */
function constructCmsUrl(cmsPath: string, previewmodel: string | null): URL {
    return new URL(
        previewmodel
            ? `${API_CMS_BASE_URL}preview/?preview_model=${previewmodel}`
            : `${API_CMS_BASE_URL}pages/find/?html_path=${cmsPath}&fields=*`
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

/**
 * Fetch block data for a block preview.
 * @param {Function} fetch - The fetch function provided by SvelteKit.
 * @param {string} blockId - The block ID of the block as given by PreviewBlocksViewSet.
 * @param {string} previewModal - The app dot model (eg. cms.DemoBlock)
 * @returns {Promise<any>} - The fetched preview data.
 */
export async function fetchBlockData(
    fetch: typeof globalThis.fetch,
    blockId: string,
    previewModal: string
): Promise<any> {
    const cmsUrl = `${API_CMS_BASE_URL}preview-block/?id=${blockId}&in_preview_panel=${previewModal}`;
    return await fetchWithErrorHandling(fetch(cmsUrl));
}

/**
 * Fetch snippet data for a snippet preview.
 * @param {Function} fetch - The fetch function provided by SvelteKit.
 * @param {string} snippetType - The app dot model of the snippet (eg. cms.DemoSnippet)
 * @param {string | null} snippetId - The ID of the snippet, if it exists already
 * @returns {Promise<any>} - The fetched preview data.
 */
export async function fetchSnippetData(
    fetch: typeof globalThis.fetch,
    snippetType: string,
    snippetId: string | null
): Promise<any> {
    const params = new URLSearchParams({ type: snippetType });

    if (snippetId) {
        params.set("id", snippetId);
    }

    const cmsUrl = `${API_CMS_BASE_URL}preview-snippet/?${params}`;
    return await fetchWithErrorHandling(fetch(cmsUrl));
}

/**
 * Constructs the URL for the Wagtail userbar based on whether the page is in preview mode.
 * @param {number} pageId - The ID of the page the userbar is used on
 * @param {string | null} previewModel - If the page is in preview mode, this will be passed.
 * @returns {URL} - The constructed URL for the CMS API.
 */
function constructUserbarUrl(pageId: number, previewModel: string | null): URL {
    const url = new URL(`${API_CMS_BASE_URL}wagtail-userbar/${pageId}/`);
    if (previewModel) {
        url.searchParams.append("in_preview_panel", previewModel);
    }
    return url;
}

export async function fetchUserbar(
    fetch: typeof globalThis.fetch,
    pageId: number,
    previewModel: string | null,
    host?: string
): Promise<WagtailUserbarType> {
    const userbarUrl = constructUserbarUrl(pageId, previewModel);
    let userbar: WagtailUserbarType = { html: "" };

    try {
        const opts: RequestInit = {};
        if (host) {
            opts.headers = { "X-Forwarded-Host": host };
        }
        const response = await fetch(userbarUrl, opts);

        if (response.ok) {
            userbar = await response.json();
        }

        if (response.status !== 403) {
            captureMessage(`${response.status} from the userbar`);
        }
    } catch (e) {
        console.error(e);
        captureException(e);
    }
    return userbar;
}
