// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { Menus } from "$lib/navigation/menus";
import type { Me } from "$lib/session/types";
// :: IF api__wagtail
import type { BlockComponents } from "$lib/utils/cms";
// :: ENDIF

declare global {
    namespace App {
        // interface Error {}
        // interface Locals {}

        /** Data available on every page, see the root layout */
        interface PageData {
            /** Menus of the site, prefer `useMenu()` to access them */
            menus: Menus;

            /** The visitor's session, prefer `useSession()` to access it */
            me: Me | null;
            // :: IF api__wagtail

            /** Components of the StreamField blocks of CMS pages */
            blockComponents?: BlockComponents;
            // :: ENDIF
        }

        // interface PageState {}
        // interface Platform {}
    }
}

export {};
