/**
 * Universal load function for Wagtail pages.
 *
 * Dynamically import the correct page component based on the meta.type field,
 * as well as the components of all the StreamField blocks found in the page
 * (see `getBlockComponents()`).
 */

import type { Component } from "svelte";
import { collectBlockTypes, getBlockComponents } from "$lib/utils/cms";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ data }) => {
    /** Get the app name and model name from the meta.type */
    const [appName, modelName] = data.pageData.meta.type.split(".");

    const [pageComponent, blockComponents] = await Promise.all([
        import(`$lib/components/${appName}/pages/${modelName}.svelte`).then(
            (m: { default: Component<any> }) => m.default
        ),
        getBlockComponents(collectBlockTypes(data.pageData)),
    ]);

    return {
        component: pageComponent,
        blockComponents,
        cmsData: data.pageData,
        userbar: data.userbar,
    };
};
