<template>
    <component
        v-for="(component, i) in asyncComponents"
        :key="i"
        :is="component"
        v-bind="props.blocks[i]"
    />
</template>

<script setup lang="ts">
/**
 * Displays a Wagtail StreamField, with a list of dynamic components all
 * corresponding to a specific bloc type.
 */

import { defineAsyncComponent } from "vue";
import { Block } from "~/types/wagtail";

const props = defineProps<{
    blocks: Block[];
}>();

// Preloading blocks allows dynamically importing them by path at runtime
const allAsyncComponents = import.meta.glob("./blocks/**/*.vue");
const asyncComponents = computed(() =>
    props.blocks.map((block) =>
        defineAsyncComponent<any>(() => {
            const componentPath = block.type.replace(".", "/");
            return allAsyncComponents[`./blocks/${componentPath}.vue`]();
        })
    )
);
</script>
