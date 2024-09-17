<template>
    <Head>
        <Title>
            {{ headData.title }}
        </Title>
    </Head>
    <ServerTemplatedComponent
        :content="html"
        :components-defs="defs"
        @head="receiveHeadData"
    />
</template>

<script setup lang="ts">
import Title1 from "@/components/blocks/title-1.vue";
import type { MetaObject } from "@nuxt/schema";
import { useLayoutStore } from "@/stores/layout.js";

const defs = {
    Title1,
};
definePageMeta({
    middleware: ["wagtail"],
});

const html = ref(useLayoutStore().pageHtml);
/**
 * Receiver for the head data from the parsed component, which allows to have
 * the proper meta info at SSR time.
 */
function receiveHeadData(head: MetaObject) {
    useHead(head);
}
</script>
