<script lang="ts">
    /**
     * Root layout: global styles and the contexts every component can rely
     * on. The visible layout (header, footer...) lives in `(site)/` so that
     * previews rendered in the CMS don't get it.
     */
    import "$lib/styles/main.scss";
    import { metaRouter } from "$lib/meta-router/config";
    import { provideMenus } from "$lib/navigation/context";
    import { provideSession } from "$lib/session/context";
    import type { Snippet } from "svelte";
    import type { LayoutData } from "./$types";

    let { data, children }: { data: LayoutData; children: Snippet } = $props();

    provideMenus(() => data.menus);
    provideSession(() => data.me, metaRouter.deps);
</script>

{@render children()}
