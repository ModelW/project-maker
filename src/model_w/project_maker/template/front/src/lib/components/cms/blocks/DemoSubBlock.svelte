<script lang="ts">
    import { page } from "$app/stores";

    export let props: any;
</script>

<h1>Demo block</h1>
<p>{props.tagline}</p>
<p>{@html props.description}</p>
{#each props.blocks as block}
    <svelte:component this={$page.data.blockComponents[block.type]} props={block.value} />
{/each}
