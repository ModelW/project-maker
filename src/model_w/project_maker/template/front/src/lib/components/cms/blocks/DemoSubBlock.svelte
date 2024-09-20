<script lang="ts">
    import { page } from "$app/stores";
    import Image from "../images/Image.svelte";

    export let props: any;
</script>

<h5>Demo Sub Block</h5>
<p>{props.tagline}</p>
<p>{@html props.description}</p>
{#each props.heading_blocks as block}
    <hr />
    <svelte:component this={$page.data.blockComponents[block.type]} props={block.value} />
    <hr />
{/each}

{#if props.image}
    <h6>Image with custom filters and media queries</h6>
    <div class="image-container">
        <Image image={props.image} />
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
