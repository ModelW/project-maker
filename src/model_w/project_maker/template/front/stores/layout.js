import { defineStore } from "pinia";

/**
 * Store for layouts. if there is any data we need to share between layouts.
 */
export const useLayoutStore = defineStore("layout", {
    state() {
        return {
            pageHtml: "",
        };
    },

    actions: {
        /**
         * Set HTML to be used with server template component.
         */
        setPageHtml(html) {
            this.pageHtml = html;
        },
    },
});
