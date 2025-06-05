/**
 * General types relating to pages but not specific to a single page.
 */

export type PageType<T = Record<string, unknown>> = {
    id: number;
    meta: {
        type: string;
        detail_url: string;
        html_url: string;
        slug: string;
        show_in_menus: boolean;
        seo_title: string;
        search_description: string;
        first_published_at: string;
        alias_of: null | number;
        parent: {
            id: number;
            meta: {
                type: string;
                detail_url: string;
                html_url: string;
            };
            title: string;
        };
        locale: string;
    };
    title: string;
} & T;

export type WagtailUserbarType = Record<"html", string>;
