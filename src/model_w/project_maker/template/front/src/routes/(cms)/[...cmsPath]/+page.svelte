<script lang="ts">
    /**
     * This page is a catch-all for all CMS pages.
     * It selects the appropriate component to render based on the template field.
     */
    import type { PageData } from "./$types";

    export let data: PageData;
</script>

<svelte:component this={data.component} cmsData={data.cmsData} />
