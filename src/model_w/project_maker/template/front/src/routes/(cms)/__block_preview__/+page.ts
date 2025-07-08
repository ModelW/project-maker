/**
 * Universal load function for Wagtail block previews.
 *
 * Dynamically import the correct block component based on the meta.type field.
 */

import type { Component } from "svelte";
import type { PageServerData } from "./$types";

export async function load({ data }: { data: PageServerData }) {
    /** Get the app name and model name from the meta.type */
    const [appName, modelName] = data.blockData.meta.type.split(".");

    /** Import the block component */
    const blockComponent: Component = (
        await import(`$lib/components/${appName}/blocks/${modelName}.svelte`)
    ).default;

    return {
        component: blockComponent,
        cmsData: { ...data.blockData },
    };
}
