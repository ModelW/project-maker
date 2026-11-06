/**
 * Content of the site's menus.
 *
 * The functions below are the single source of the header and footer menus.
 * They are static for now but deliberately async and handed SvelteKit's
 * `fetch`: when the menus need to come from the CMS or the API, only the body
 * of the functions has to change, not their callers.
 *
 * They are called once by the root layout's server load and exposed to all
 * components through `useMenu()` (see `./context.ts`).
 */

/** An entry of a menu which leads somewhere */
export interface MenuLink {
    /** Text displayed to the user */
    label: string;

    /** Where the entry leads */
    href: string;
}

/** An entry of a menu which groups other entries (dropdown, footer column) */
export interface MenuGroup {
    /** Text displayed to the user */
    label: string;

    /** Sub-entries */
    children: MenuItem[];
}

/** An entry of a menu */
export type MenuItem = MenuLink | MenuGroup;

/**
 * Tells apart groups from links
 *
 * @param item The menu entry
 */
export function isMenuGroup(item: MenuItem): item is MenuGroup {
    return "children" in item;
}

/** Names of the menus available through `useMenu()` */
export type MenuName = "header" | "footer";

/** All the menus of the site, by name */
export type Menus = Record<MenuName, MenuItem[]>;

/**
 * Items of the main navigation, displayed in the header (and in the drawer on
 * mobile).
 *
 * @param _fetch SvelteKit's fetch, to be used if the menu comes from the API
 */
// eslint-disable-next-line @typescript-eslint/require-await
export async function getHeaderMenu(
    _fetch: typeof globalThis.fetch
): Promise<MenuItem[]> {
    return [
        { label: "Home", href: "/" },
        // :: IF api__testing
        { label: "Demo", href: "/demo/" },
        // :: ENDIF
        // :: IF api__wagtail
        { label: "Non-CMS", href: "/non-cms" },
        // :: ENDIF
        {
            label: "About",
            children: [
                { label: "The project", href: "/#project" },
                { label: "The team", href: "/#team" },
            ],
        },
    ];
}

/**
 * Items displayed in the footer.
 *
 * @param _fetch SvelteKit's fetch, to be used if the menu comes from the API
 */
// eslint-disable-next-line @typescript-eslint/require-await
export async function getFooterMenu(
    _fetch: typeof globalThis.fetch
): Promise<MenuItem[]> {
    return [
        {
            label: "___project_name__natural___",
            children: [
                { label: "Home", href: "/" },
                // :: IF api__testing
                { label: "Demo", href: "/demo/" },
                // :: ENDIF
            ],
        },
        // :: IF api__enable
        {
            label: "Administration",
            children: [
                // :: IF api__wagtail
                { label: "CMS", href: "/back/___admin_prefix___/cms/" },
                // :: ENDIF
                { label: "Django admin", href: "/back/___admin_prefix___/admin/" },
            ],
        },
        // :: ENDIF
    ];
}

/**
 * Loads all the menus at once.
 *
 * @param fetch SvelteKit's fetch
 */
export async function getMenus(fetch: typeof globalThis.fetch): Promise<Menus> {
    const [header, footer] = await Promise.all([
        getHeaderMenu(fetch),
        getFooterMenu(fetch),
    ]);
    return { header, footer };
}
