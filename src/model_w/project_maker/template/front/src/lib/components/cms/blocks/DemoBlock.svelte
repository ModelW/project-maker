<script lang="ts">
    import { page } from "$app/stores";
    import Image from "../images/Image.svelte";

    export let props: any;
</script>

<h3>Demo block</h3>
<p>{props.tagline}</p>
<p>{@html props.description}</p>
{#each props.demo_sub_blocks as block}
    <hr />
    <svelte:component this={$page.data.blockComponents[block.type]} props={block.value} />
    <hr />
{/each}

{#if props.image}
    <h4>Default image (without filters specified)</h4>
    <div class="image-container">
        <Image image={props.image} />
    </div>
{/if}

<style lang="scss">
    .image-container {
        // Layout
        height: 350px;
        width: 100%;
        overflow: hidden;
        // Styling
        border-radius: 30px;
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
    }
</style>
