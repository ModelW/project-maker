<script lang="ts">
    /**
     * Renders the blocks of a StreamField, at any depth: each block is
     * rendered by the component of the same name in `blocks/`, as loaded by
     * `getBlockComponents()` into the page data.
     *
     * Blocks without a matching component are skipped (create the component
     * to have them rendered).
     */
    import { page } from "$app/state";
    import type { StreamFieldBlock } from "$lib/utils/cms";

    let { blocks }: { blocks: StreamFieldBlock[] } = $props();
</script>

{#each blocks as block, i (block.id ?? i)}
    {@const BlockComponent = page.data.blockComponents?.[block.type]}
    {#if BlockComponent}
        <BlockComponent cmsData={block.value} />
    {/if}
{/each}
