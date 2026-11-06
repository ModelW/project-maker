<script lang="ts">
    /**
     * This page displays preview data for all CMS block previews.
     * It selects the appropriate component to render based on the meta.type.
     */
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();
</script>

<data.component cmsData={data.cmsData} />
