/**
 * Universal load function for Wagtail snippet previews.
 *
 * Dynamically import the correct snippet component based on the meta.type
 * field, as well as the components of the StreamField blocks it contains.
 */

import type { Component } from "svelte";
import { collectBlockTypes, getBlockComponents } from "$lib/utils/cms";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ data }) => {
    /** Get the app name and model name from the meta.type (e.g. "cms.DemoSnippet"). */
    const [appName, modelName] = data.snippetData.meta.type.split(".");

    const [snippetComponent, blockComponents] = await Promise.all([
        import(`$lib/components/${appName}/snippets/${modelName}.svelte`).then(
            (m: { default: Component<any> }) => m.default
        ),
        getBlockComponents(collectBlockTypes(data.snippetData)),
    ]);

    return {
        component: snippetComponent,
        blockComponents,
        cmsData: { ...data.snippetData },
    };
};
