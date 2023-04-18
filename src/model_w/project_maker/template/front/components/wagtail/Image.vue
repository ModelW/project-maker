<template>
    <img
        :src="image.rendition.url"
        :alt="image.rendition.alt"
        :width="image.rendition.width"
        :height="image.rendition.height"
    />
</template>

<script setup lang="ts">
/**
 * Fetches and displays a Wagtail image with a specific rendition, according to
 * the spec sent as prop.
 */
import { Image as WagtailImage } from "~/types/wagtail";

const { $axios } = useNuxtApp();
const { imageId, spec } = defineProps<{
    imageId: number;
    spec: string;
}>();

let image: any

try {
    image = await $axios.$get<WagtailImage>(
        `/back/images/${imageId}/?image_spec=${spec}`
    );
} catch (e) {
    console.error(e);
}
</script>
