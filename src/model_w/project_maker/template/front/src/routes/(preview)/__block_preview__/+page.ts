/**
 * Universal load function for Wagtail block previews.
 *
 * Dynamically import the correct block component based on the meta.type field,
 * as well as the components of the blocks nested in it.
 */

import type { Component } from "svelte";
import { collectBlockTypes, getBlockComponents } from "$lib/utils/cms";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ data }) => {
    /** Get the app name and model name from the meta.type */
    const [appName, modelName] = data.blockData.meta.type.split(".");

    const [blockComponent, blockComponents] = await Promise.all([
        import(`$lib/components/${appName}/blocks/${modelName}.svelte`).then(
            (m: { default: Component<any> }) => m.default
        ),
        getBlockComponents(collectBlockTypes(data.blockData)),
    ]);

    return {
        component: blockComponent,
        blockComponents,
        cmsData: { ...data.blockData },
    };
};
