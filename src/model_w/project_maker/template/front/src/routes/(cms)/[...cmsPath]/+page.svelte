<script lang="ts">
    /**
     * This page is a catch-all for all CMS pages.
     * It selects the appropriate component to render based on the template field.
     */
    import type { PageData } from "./$types";

    export let data: PageData;
</script>

<svelte:head>
    <title>{data.cmsData.meta.seo_title || data.cmsData.title}</title>
    <meta name="description" content={data.cmsData.meta.search_description} />
</svelte:head>

{@html data.userbar.html}

<svelte:component this={data.component} cmsData={data.cmsData} />
