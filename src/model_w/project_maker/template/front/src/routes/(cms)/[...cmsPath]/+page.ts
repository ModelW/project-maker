/**
 * Universal load function for Wagtail pages.
 *
 * Dynamically import the correct page component based on the meta.type field.
 * Furthermore, dynamically import all the block components and store them in
 * the blockComponents object.
 */

import type { ComponentType } from "svelte";
import type { PageServerData } from "./$types";

export async function load({ data }: { data: PageServerData }) {
    /** Get the app name and model name from the meta.type */
    const [appName, modelName] = data.pageData.meta.type.split(".");

    const pageComponent: ComponentType = (
        await import(`$lib/components/${appName}/pages/${modelName}.svelte`)
    ).default;

    return {
        component: pageComponent,
        cmsData: { ...data.pageData },
    };
}
