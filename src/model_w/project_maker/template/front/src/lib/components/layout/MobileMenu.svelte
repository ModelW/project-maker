<script lang="ts">
    /**
     * Burger button opening the main navigation in a drawer, for small
     * screens. The drawer (https://github.com/harshmandan/svaul) handles
     * focus trapping, scroll locking, Escape and swipe-to-dismiss.
     */
    import Drawer from "@harshmandan/svaul";
    import { afterNavigate } from "$app/navigation";
    import type { MenuItem } from "$lib/navigation/menus";
    import NavList from "./NavList.svelte";

    let { items }: { items: MenuItem[] } = $props();

    let open = $state(false);

    afterNavigate(() => {
        open = false;
    });
</script>

<Drawer bind:open direction="right" ariaLabel="Menu" class="mobile-menu" data-testid="mobile menu">
    {#snippet trigger(props)}
        <button
            {...props}
            type="button"
            class="burger"
            aria-label="Open the menu"
            data-testid="mobile menu button"
        >
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path
                    d="M3 6h18M3 12h18M3 18h18"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />
            </svg>
        </button>
    {/snippet}

    <nav aria-label="Main">
        <NavList {items} variant="drawer" onnavigate={() => (open = false)} />
    </nav>

    {#snippet footer({ close })}
        <button type="button" class="close" onclick={close}>Close</button>
    {/snippet}
</Drawer>

<style lang="scss">
    .burger {
        display: grid;
        place-items: center;
        width: 2.5rem;
        height: 2.5rem;
        cursor: pointer;

        svg {
            width: 1.5rem;
            height: 1.5rem;
        }
    }

    // The drawer is rendered in a portal, out of this component's scope
    :global(.mobile-menu) {
        width: min(20rem, 85vw);
        height: 100%;
        padding: 1.5rem 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        overflow-y: auto;
        // Svaul extends the drawer past its edge (::after) so that flinging it
        // doesn't reveal a gap: that must not become horizontal scroll
        overflow-x: hidden;
        background: var(--surface-color, #fff);
    }

    .close {
        align-self: flex-start;
        padding: 0.5em 0.75em;
        cursor: pointer;
        text-decoration: underline;
    }
</style>
