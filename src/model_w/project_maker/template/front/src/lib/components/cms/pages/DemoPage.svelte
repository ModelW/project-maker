<script lang="ts">
    import { page } from "$app/stores";
    import { onMount } from "svelte";

    export let props: any;

    let hasHydrated = false;

    onMount(() => {
        hasHydrated = true;
    });
</script>

<em>Hydration status: {hasHydrated}</em>
<hr />

<main data-testid="demo page">
    <h1>{props.title}</h1>
    <p>{@html props.description}</p>
    {#each props.blocks as block}
        <hr />
        <svelte:component this={$page.data.blockComponents[block.type]} props={block.value} />
    {/each}
</main>
