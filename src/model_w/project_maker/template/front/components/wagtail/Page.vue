<template>
    <component :is="asyncComponent" v-bind="page" />
</template>

<script setup lang="ts">
    /**
     * This component is the entrypoint to display Wagtail pages. Depending on the
     * current route path, it fetches page data from the API, and uses a dynamic
     * component according to the page type.
     */

    import { defineAsyncComponent } from "vue";
    import { Page } from "~/types/wagtail";

    const { $axios } = useNuxtApp();
    const props = withDefaults(
        defineProps<{
            draft: boolean;
        }>(),
        {
            draft: false,
        }
    );

    // Preloading pages allows dynamically importing them by path at runtime
    const allAsyncComponents = import.meta.glob("./pages/**/*.vue");
    const route = useRoute();
    const pageIdMatch = route.path.match(/\/pages\/([^/]+)/);
    const pageId = pageIdMatch ? parseInt(pageIdMatch[1]) : null;
    const draftParam = `draft=${props.draft ? "true" : "false"}`;
    const url = pageId
        ? `/back/pages/${pageId}/?${draftParam}`
        : `/back/pages/find/?html_path=${route.path}&${draftParam}`;
    const page = await $axios.$get<Page>(url,
        {
            headers: { "x-reach-api": "true" },
        }
    );
    const asyncComponent = defineAsyncComponent<any>(async () => {
        try {
            // Getting from allAsyncComponents the component we want to render
            const componentPath = `./pages/${page.meta.type.replace(".", "/")}.vue`;
            const componentFunction = allAsyncComponents[componentPath]
            return componentFunction();
        } catch (e) {
            console.error(e);
            return import("./pages/LoadingError.vue");
        }
    });
</script>
