<template>
    <div>
        <h1>{{ title }}</h1>
        <div v-html="main_text" />
        <Image :image-id="main_image.id" spec="fill-300x300" />
        <StreamField :blocks="content" />
        <Toast />
    </div>
</template>

<script setup lang="ts">
import { Block, ImageInfo } from "~/types/wagtail";
import Image from "~/components/wagtail/Image.vue";
import StreamField from "~/components/wagtail/StreamField.vue";
import Toast from "~/components/wagtail/Toast.vue";

defineProps<{
    title?: string;
    main_text?: string;
    main_image?: ImageInfo;
    content: Block[];
}>();
</script>
