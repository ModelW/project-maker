<script lang="ts">
    /**
     * Renders a menu as an accessible list of links. Items with children get
     * a disclosure button (`aria-expanded`) which toggles their sub-menu on
     * click, and also on hover with a mouse in the "bar" variant.
     *
     * - `bar`: horizontal, sub-menus drop down (desktop header)
     * - `drawer`: vertical, sub-menus open inline (mobile drawer)
     */
    import { afterNavigate } from "$app/navigation";
    import { page } from "$app/state";
    import { isMenuGroup, type MenuItem } from "$lib/navigation/menus";
    import type { Attachment } from "svelte/attachments";
    import NavList from "./NavList.svelte";

    interface Props {
        /** Items to display */
        items: MenuItem[];

        /** How the list is displayed */
        variant?: "bar" | "drawer";

        /** Nesting depth, 0 for the root list */
        level?: number;

        /** ID of the list, so that a disclosure button can control it */
        id?: string;

        /** Called when a link of the menu (at any depth) gets clicked */
        onnavigate?: () => void;
    }

    let { items, variant = "bar", level = 0, id, onnavigate }: Props = $props();

    const uid = $props.id();

    /** Delay before closing a sub-menu when the mouse leaves it */
    const HOVER_CLOSE_DELAY = 200;

    let openIndex: number | null = $state(null);

    /**
     * Whether the open sub-menu was opened by hovering it. In that case a
     * click (which comes right after the pointer entered) keeps it open
     * instead of closing it.
     */
    let openedByHover = false;
    let closeTimer: ReturnType<typeof setTimeout> | undefined;
    let root: HTMLUListElement | undefined = $state();

    const hoverable = $derived(variant === "bar");

    function toggle(index: number): void {
        if (openIndex === index && openedByHover) {
            openedByHover = false;
            return;
        }

        openedByHover = false;
        openIndex = openIndex === index ? null : index;
    }

    function onPointerEnter(event: PointerEvent, index: number): void {
        if (!hoverable || event.pointerType !== "mouse") {
            return;
        }

        clearTimeout(closeTimer);

        if (openIndex !== index) {
            openIndex = index;
            openedByHover = true;
        }
    }

    function onPointerLeave(event: PointerEvent, index: number): void {
        if (!hoverable || event.pointerType !== "mouse") {
            return;
        }

        clearTimeout(closeTimer);
        closeTimer = setTimeout(() => {
            if (openIndex === index && openedByHover) {
                openIndex = null;
                openedByHover = false;
            }
        }, HOVER_CLOSE_DELAY);
    }

    function onKeyDown(event: KeyboardEvent, index: number): void {
        if (event.key === "Escape" && openIndex === index) {
            event.stopPropagation();
            openIndex = null;
            root?.querySelector<HTMLButtonElement>(`#${uid}-${index}-button`)?.focus();
        }
    }

    /**
     * Hover and Escape handling of a sub-menu. This only enhances the
     * disclosure button, which remains the way to open it with a keyboard or
     * a touch screen.
     *
     * @param index Index of the item that has a sub-menu
     */
    function disclosure(index: number): Attachment<HTMLLIElement> {
        return (node) => {
            const enter = (e: PointerEvent) => onPointerEnter(e, index);
            const leave = (e: PointerEvent) => onPointerLeave(e, index);
            const keydown = (e: KeyboardEvent) => onKeyDown(e, index);

            node.addEventListener("pointerenter", enter);
            node.addEventListener("pointerleave", leave);
            node.addEventListener("keydown", keydown);

            return () => {
                node.removeEventListener("pointerenter", enter);
                node.removeEventListener("pointerleave", leave);
                node.removeEventListener("keydown", keydown);
            };
        };
    }

    function onWindowClick(event: MouseEvent): void {
        if (openIndex !== null && root && !root.contains(event.target as Node)) {
            openIndex = null;
        }
    }

    function isCurrent(href: string): boolean {
        const url = new URL(href, page.url);
        return url.pathname === page.url.pathname && url.hash === page.url.hash;
    }

    /**
     * Closes the menu when one of its links is followed. afterNavigate()
     * covers most cases, but not a link to the current page with another
     * hash, which isn't a navigation for SvelteKit.
     */
    function onLinkClick(): void {
        openIndex = null;
        openedByHover = false;
        onnavigate?.();
    }

    afterNavigate(() => {
        openIndex = null;
    });
</script>

<svelte:window onclick={onWindowClick} />

<ul bind:this={root} {id} class="nav-list {variant}" class:root={level === 0}>
    {#each items as item, i (i)}
        {#if isMenuGroup(item)}
            <li class="has-children" {@attach disclosure(i)}>
                <button
                    id="{uid}-{i}-button"
                    type="button"
                    class="item"
                    aria-expanded={openIndex === i}
                    aria-controls="{uid}-{i}"
                    onclick={() => toggle(i)}
                >
                    {item.label}
                    <svg
                        class="chevron"
                        viewBox="0 0 12 12"
                        aria-hidden="true"
                        focusable="false"
                    >
                        <path
                            d="M2 4l4 4 4-4"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.5"
                        />
                    </svg>
                </button>
                <div class="sub-menu" hidden={openIndex !== i}>
                    <NavList
                        items={item.children}
                        {variant}
                        level={level + 1}
                        id="{uid}-{i}"
                        onnavigate={onLinkClick}
                    />
                </div>
            </li>
        {:else}
            <li>
                <a
                    class="item"
                    href={item.href}
                    onclick={onLinkClick}
                    aria-current={isCurrent(item.href) ? "page" : undefined}
                >
                    {item.label}
                </a>
            </li>
        {/if}
    {/each}
</ul>

<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;

    .nav-list {
        @include mixins.reset-list;
    }

    li {
        position: relative;
    }

    .item {
        display: flex;
        align-items: center;
        gap: 0.25em;
        padding: 0.5em 0.75em;
        border-radius: 0.375em;
        color: inherit;
        text-decoration: none;
        cursor: pointer;

        &:focus-visible {
            background: rgb(0 0 0 / 6%);
        }

        // Touch screens keep :hover stuck on the last tapped element
        @media (hover: hover) {
            &:hover {
                background: rgb(0 0 0 / 6%);
            }
        }

        &[aria-current="page"] {
            font-weight: 600;
        }
    }

    .chevron {
        width: 0.75em;
        height: 0.75em;
        transition: rotate 150ms ease;
    }

    [aria-expanded="true"] .chevron {
        rotate: 180deg;
    }

    .bar.root {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .bar.root > li > .sub-menu {
        position: absolute;
        top: 100%;
        left: 0;
        min-width: 12rem;
        padding: 0.5rem;
        border-radius: 0.5rem;
        background: var(--surface-color, #fff);
        box-shadow: 0 0.5rem 1.5rem rgb(0 0 0 / 15%);
    }

    // The last items sit against the end of the header: align their sub-menu
    // to the right so that it does not overflow the viewport.
    .bar.root > li:last-child > .sub-menu {
        right: 0;
        left: auto;
    }

    .nav-list:not(.root) .sub-menu,
    .drawer .sub-menu {
        padding-left: 1rem;
    }

    .drawer .item {
        width: 100%;
        padding-block: 0.75em;
    }
</style>
