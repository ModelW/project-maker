<script lang="ts">
    /**
     * Layout of the pages of the site: fixed header, content and footer.
     * Previews rendered inside the CMS are outside of this group, so they
     * don't get the header and footer.
     */
    import Footer from "$lib/components/layout/Footer.svelte";
    import Header from "$lib/components/layout/Header.svelte";
    import type { Snippet } from "svelte";

    let { children }: { children: Snippet } = $props();
</script>

<a class="skip-link" href="#main">Skip to content</a>

<Header />

<main id="main" class="main">
    {@render children()}
</main>

<Footer />

<style lang="scss">
    .main {
        // Pushes the content below the fixed header
        padding-top: var(--header-height);

        // The content fills at least the screen, so the footer never floats
        // mid-page. `svh` is the viewport height with the mobile browser's
        // toolbars visible: unlike `vh` the content doesn't end up behind
        // them, and unlike `dvh` it doesn't change size while scrolling. `vh`
        // remains as a fallback for older browsers.
        min-height: 100vh;
        min-height: 100svh;
    }

    .skip-link {
        position: absolute;
        top: 0;
        left: 0;
        z-index: 1000;
        padding: 0.5rem 1rem;
        background: var(--surface-color, #fff);
        translate: 0 -100%;

        &:focus {
            translate: 0 0;
        }
    }
</style>
