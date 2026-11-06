<script lang="ts">
    import StreamField from "$lib/components/cms/StreamField.svelte";
    import Image from "$lib/components/cms/images/Image.svelte";

    let { cmsData }: { cmsData: any } = $props();
</script>

<h5>Demo Sub Block</h5>
<p>{cmsData.tagline}</p>
<div>{@html cmsData.description}</div>
<StreamField blocks={cmsData.heading_blocks} />

{#if cmsData.image}
    <h6>Image with custom filters and media queries</h6>
    <div class="image-container">
        <Image image={cmsData.image} />
    </div>
{/if}

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;

    .image-container {
        // Variables
        --image-width: 100%;
        --image-height: 150px;

        // Layout
        height: var(--image-height);
        width: var(--image-width);
        overflow: hidden;

        // Styling
        border-radius: 30px;
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);

        @include mixins.breakpoints-up(md) {
            --image-width: 50%;
            --image-height: 250px;
        }

        @include mixins.breakpoints-up(lg) {
            --image-width: 25%;
            --image-height: 350px;
        }
    }
</style>
