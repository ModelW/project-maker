import adapter from "@sveltejs/adapter-node";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
    // Consult https://kit.svelte.dev/docs/integrations#preprocessors
    // for more information about preprocessors
    preprocess: vitePreprocess(),

    kit: {
        adapter: adapter(),
        // Django will check this, so as long as nothing extravagant happens
        // in the front-end, we don't need Svelte to check it.
        csrf: {
            checkOrigin: false,
        },
    },
};

export default config;
