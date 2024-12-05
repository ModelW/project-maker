<script lang="ts">
    import Image from "$lib/components/cms/images/Image.svelte";

    export let cmsData: any;
</script>

<h5>Demo Sub Block</h5>
<p>{cmsData.tagline}</p>
<p>{@html cmsData.description}</p>
{#each cmsData.heading_blocks as block}
    <hr />
    {#if block.type === "Heading"}
        <h6>{block.value}</h6>
        <hr />
    {/if}
{/each}

{#if cmsData.image}
    <h6>Image with custom filters and media queries</h6>
    <div class="image-container">
        <Image image={cmsData.image} />
    </div>
{/if}

<style lang="scss">
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

        @media screen and (min-width: 768px) {
            --image-width: 50%;
            --image-height: 250px;
        }

        @media screen and (min-width: 1024px) {
            --image-width: 25%;
            --image-height: 350px;
        }
    }
</style>
