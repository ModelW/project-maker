<script lang="ts">
    /**
     * This page is a catch-all for all CMS pages.
     * It selects the appropriate component to render based on the template field.
     */
    import { browser } from "$app/env";
    import { runScripts } from "$lib/utils/runScripts";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let hasHydrated: boolean = $state(false);

    $effect(() => {
        if (browser) {
            hasHydrated = true;
        }
    });
</script>

<svelte:head>
    <title>{data.cmsData.meta.seo_title || data.cmsData.title}</title>
    <meta name="description" content={data.cmsData.meta.search_description} />
</svelte:head>

{#if hasHydrated}
    <div use:runScripts>{@html data.userbar.html}</div>
{/if}

<data.component cmsData={data.cmsData} />
