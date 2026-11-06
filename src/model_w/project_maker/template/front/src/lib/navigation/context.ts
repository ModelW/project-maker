/**
 * Makes the menus loaded by the root layout available to any component,
 * without having to drill them down through props.
 */

import { createContext } from "svelte";
import type { MenuItem, MenuName, Menus } from "./menus";

const [getMenus, setMenus] = createContext<() => Menus>();

/**
 * Registers the menus for the whole component tree. Called once by the root
 * layout.
 *
 * @param menus Getter returning the menus, so that the context follows the
 *              page data when it gets invalidated
 */
export function provideMenus(menus: () => Menus): void {
    setMenus(menus);
}

/**
 * Gives access to a menu from anywhere in the app.
 *
 * Like any Svelte context, this must be called during the component's
 * initialisation (at the top level of its `<script>`), not in an event
 * handler or an effect. The returned object is reactive.
 *
 * @example
 * ```svelte
 * <script lang="ts">
 *     const menu = useMenu("footer");
 * </script>
 *
 * {#each menu.items as item (item.href)}
 *     <a href={item.href}>{item.label}</a>
 * {/each}
 * ```
 *
 * @param name Name of the menu
 */
export function useMenu(name: MenuName): { readonly items: MenuItem[] } {
    const menus = getMenus();

    return {
        get items() {
            return menus()[name];
        },
    };
}
