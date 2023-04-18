<template>
    <p>{{ value }}</p>
</template>

<script setup lang="ts">
import { Block } from "~/types/wagtail";

export interface Content extends Block {
    type: "text";
    value: string;
}

defineProps<Content>();
</script>
