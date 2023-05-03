import { defineNuxtPlugin } from "nuxt/app";
import { JSDOM } from "jsdom";

/**
 * Converts HTML source code into DOM-like content.
 *
 * On the server this uses the JSDOM lib while on the browser it uses the real
 * DOM API.
 *
 * @param html {string} HTML code you want to parse
 * @return {Document}
 */
function htmlToDom(html): Document {
    const { document: mockDocument } = new JSDOM(html).window;
    return mockDocument;
}

export default defineNuxtPlugin(() => ({ provide: { htmlToDom } }));
