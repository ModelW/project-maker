/**
 * Converts HTML source code into DOM-like content.
 *
 * On the server this uses the JSDOM lib while on the browser it uses the real
 * DOM API.
 *
 * @param html {string} HTML code you want to parse
 * @return {Document}
 */
export function htmlToDom(html) {
    const parser = new DOMParser();
    return parser.parseFromString(html, "text/html");
}

export default defineNuxtPlugin(() => ({ provide: { htmlToDom } }));
