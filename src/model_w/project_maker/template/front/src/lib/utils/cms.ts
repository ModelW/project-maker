/**
 * Utility functions for working with the CMS.
 */

import type { ComponentType } from "svelte";

/**
 * To have a block know how to render itself just from its own type (matching to a Svelte Component in blocks/),
 * and have SSR work, the server imports all block components and makes them available at $page.blockComponents.
 * Then they can be rendered as follows:
 * ```svelte
 *  {#each props.blocks as block}
 *      <svelte:component this={$page.data.blockComponents[block.type]} props={block.value} />
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
