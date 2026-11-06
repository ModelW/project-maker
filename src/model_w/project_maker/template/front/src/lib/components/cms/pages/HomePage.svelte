<script lang="ts">
    import type { PageType } from "./types";

    let { cmsData }: { cmsData: PageType } = $props();
</script>

<article class="container" data-testid="home page">
    <h1>{cmsData.title}</h1>
</article>
