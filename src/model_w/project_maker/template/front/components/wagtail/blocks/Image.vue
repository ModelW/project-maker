<template>
    <Image :image-id="value" spec="fill-500x500" />
</template>

<script setup lang="ts">
import { Block } from "~/types/wagtail";
import Image from '../Image.vue'

export interface Content extends Block {
    type: "image";
    value: number;
}

defineProps<Content>();
</script>
