<script lang="ts">
    import { onMount } from "svelte";
    import Image from "$lib/components/cms/images/Image.svelte";
    import DemoBlock from "$lib/components/cms/blocks/DemoBlock.svelte";

    export let cmsData: any;

    let hasHydrated = false;

    onMount(() => {
        hasHydrated = true;
    });
</script>

<em>Hydration status: {hasHydrated}</em>
<hr />

<main data-testid="demo page">
    <h1>{cmsData.title}</h1>
    <p>{@html cmsData.description}</p>
    {#each cmsData.demo_blocks as block}
        <hr />
        {#if block.type === "DemoBlock"}
            <svelte:component this={DemoBlock} cmsData={block.value} />
        {/if}
    {/each}

    {#if cmsData.image}
        <h2>An image with fill-widthxheight (100% centred focal point)</h2>
        <div class="image-container">
            <Image image={cmsData.image} />
        </div>
    {/if}
</main>

<style lang="scss">
    :global(main) {
        max-width: 1440px;
        margin: 0 auto;
        padding: 50px;
    }

    :global(:root, body, html) {
        box-sizing: border-box;
        padding: 0;
        margin: 0;
        width: 100%;
        min-height: 100%;
    }

    .image-container {
        // Layout
        height: 300px;
        width: 100%;
        overflow: hidden;

        // Styling
        border-radius: 30px;
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
    }
</style>
