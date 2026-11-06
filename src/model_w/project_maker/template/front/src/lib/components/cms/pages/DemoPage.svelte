<script lang="ts">
    import StreamField from "$lib/components/cms/StreamField.svelte";
    import Image from "$lib/components/cms/images/Image.svelte";

    let { cmsData }: { cmsData: any } = $props();

    let hasHydrated = $state(false);

    $effect(() => {
        hasHydrated = true;
    });
</script>

<article class="container" data-testid="demo page">
    <em>Hydration status: {hasHydrated}</em>
    <hr />

    <h1>{cmsData.title}</h1>
    <div>{@html cmsData.description}</div>
    <StreamField blocks={cmsData.demo_blocks} />

    {#if cmsData.image}
        <h2>An image with fill-widthxheight (100% centred focal point)</h2>
        <div class="image-container">
            <Image image={cmsData.image} />
        </div>
    {/if}
</article>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;

    h1 {
        @include mixins.breakpoints-down(md) {
            color: lime;
        }
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
