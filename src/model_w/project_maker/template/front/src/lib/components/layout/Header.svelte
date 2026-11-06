<script lang="ts">
    /**
     * Fixed header of the site: logo and main navigation (or burger on small
     * screens).
     *
     * It shrinks as the page scrolls thanks to a scroll-driven CSS animation,
     * without any JavaScript. Browsers without support for scroll-driven
     * animations (and visitors who prefer reduced motion) simply get a header
     * that doesn't shrink.
     */
    import { useMenu } from "$lib/navigation/context";
    import Logo from "./Logo.svelte";
    import MobileMenu from "./MobileMenu.svelte";
    import NavList from "./NavList.svelte";

    const menu = useMenu("header");
</script>

<header class="header" data-testid="site header">
    <div class="container inner">
        <a class="logo" href="/" aria-label="___project_name__natural___ — Home">
            <Logo />
        </a>

        <nav class="desktop" aria-label="Main">
            <NavList items={menu.items} variant="bar" />
        </nav>

        <div class="mobile">
            <MobileMenu items={menu.items} />
        </div>
    </div>
</header>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;

    /// How much scrolling it takes to fully shrink the header
    $shrink-distance: 8rem;

    .header {
        position: fixed;
        inset: 0 0 auto;
        z-index: 100;
        height: var(--header-height);
        display: flex;
        align-items: center;
        background: var(--surface-color, #fff);
    }

    .inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }

    .logo {
        display: block;
        width: 3rem;
        height: 3rem;
        color: inherit;
        transform-origin: left center;
    }

    .desktop {
        @include mixins.breakpoints-down(md) {
            display: none;
        }
    }

    .mobile {
        @include mixins.breakpoints-up(md) {
            display: none;
        }
    }

    @supports (animation-timeline: scroll()) {
        @media (prefers-reduced-motion: no-preference) {
            .header,
            .logo {
                animation-timing-function: linear;
                animation-fill-mode: both;
                animation-timeline: scroll(root);
                animation-range: 0 $shrink-distance;
            }

            .header {
                animation-name: shrink-header;
            }

            .logo {
                animation-name: shrink-logo;
            }
        }
    }

    @keyframes shrink-header {
        to {
            height: calc(var(--header-height) * 0.7);
            box-shadow: 0 0.25rem 1rem rgb(0 0 0 / 10%);
        }
    }

    @keyframes shrink-logo {
        to {
            scale: 0.75;
        }
    }
</style>
