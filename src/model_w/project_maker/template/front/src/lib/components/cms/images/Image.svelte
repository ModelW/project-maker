<script lang="ts">
    /**
     * A responsive image component to be used for images from the API.
     *
     * The API will give the following image data:
     *
     * {
     *   "id": "image-id",
     *   "title": "Image Title",
     *   "url": "https://images.com/photo-1",
     *   "alt": "Image Alt",
     *   "width": 1000,
     *   "height": 600,
     *   "renditions": [
     *      { width: 640, url: "https://images.com/photo-2"},
     *          ...
     *    ]
     * }
     *
     * @prop {image} image - The image data from the API.
     *
     * The image is a picture tag with a source tag for each image rendition and a media query for each width.
     */

    export let image: any;
</script>

<picture>
    {#each image.renditions as rendition}
        <source srcset={rendition.url} media={rendition.media_query} />
    {/each}
    <img src={image.url} alt={image.alt} />
</picture>

<style lang="scss">
    img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
</style>
