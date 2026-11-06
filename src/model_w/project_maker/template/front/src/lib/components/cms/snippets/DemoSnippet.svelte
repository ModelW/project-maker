<script lang="ts">
    /**
     * Front-end counterpart of the `DemoSnippet` snippet, rendered by the
     * snippet preview (`/__snippet_preview__`). Snippet components live in
     * this folder and are named after their model.
     */
    let { cmsData }: { cmsData: { title: string; description: string } } = $props();
</script>

<article class="container" data-testid="demo snippet">
    <h1>{cmsData.title}</h1>
    <!-- Rich text written by the editors in the CMS, trusted by definition -->
    <!-- eslint-disable-next-line svelte/no-at-html-tags -->
    {@html cmsData.description}
</article>
