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
     *   "sources": [
     *     {
     *       "image_type": "image/webp",
     *       "srcset": [
     *         "https://images.com/photo-1-320w.webp 320w",
     *         "https://images.com/photo-1-640w.webp 640w",
     *         "https://images.com/photo-1-1280w.webp 1280w"
     *       ],
     *       "media": "(max-width: 768px)",
     *       "sizes": "100vw"
     *     },
     *     {
     *       "image_type": "image/jpeg",
     *       "srcset": [
     *         "https://images.com/photo-1-320w.jpg 320w",
     *         "https://images.com/photo-1-640w.jpg 640w",
     *         "https://images.com/photo-1-1280w.jpg 1280w"
     *       ],
     *       "media": "(min-width: 769px)",
     *       "sizes": "50vw"
     *     }
     *   ]
     * }
     *
     * @prop {image} image - The image data from the API.
     *
     * The image is a picture tag with a source tag for each image rendition and a media query for each width.
     */

    export let image: any;
</script>

<picture>
    {#each image.sources as source}
        <source
            srcset={source.srcset.join(", ")}
            type="image/{source.image_type}"
            media={source.media}
            sizes={source.sizes}
        />
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
