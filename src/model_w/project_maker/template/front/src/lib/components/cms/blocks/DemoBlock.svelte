<script lang="ts">
    import StreamField from "$lib/components/cms/StreamField.svelte";
    import Image from "$lib/components/cms/images/Image.svelte";

    let { cmsData }: { cmsData: any } = $props();
</script>

<h3>Demo block</h3>
<p>{cmsData.tagline}</p>
<div>{@html cmsData.description}</div>
<StreamField blocks={cmsData.demo_sub_blocks} />

{#if cmsData.image}
    <h4>Default image (without filters specified)</h4>
    <div class="image-container">
        <Image image={cmsData.image} />
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
