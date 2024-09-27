<script lang="ts">
    import Image from "$lib/components/cms/images/Image.svelte";
    import DemoSubBlock from "$lib/components/cms/blocks/DemoSubBlock.svelte";

    export let props: any;
</script>

<h3>Demo block</h3>
<p>{props.tagline}</p>
<p>{@html props.description}</p>
{#each props.demo_sub_blocks as block}
    <hr />
    {#if block.type === "DemoSubBlock"}
        <svelte:component this={DemoSubBlock} props={block.value} />
        <hr />
    {/if}
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
