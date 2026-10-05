/**
 * Execute the <script> tags contained within a node.
 *
 * Browsers do not execute scripts inserted via `innerHTML` (i.e. Svelte's `{@html}`),
 * and some embedded widgets (such as the Wagtail userbar) ship their behaviour in
 * `<script>` tags.
 *
 * Each script is only ever executed once (tracked by its `src`, or its inline contents as a
 * fallback), so repeated mounts and client-side navigations won't reload assets or
 * re-register things like custom elements.
 */
const executed = new Set<string>();

export function runScripts(node: HTMLElement): void {
    for (const script of node.querySelectorAll("script")) {
        const key = script.src || script.textContent || "";

        if (executed.has(key)) {
            continue;
        }

        executed.add(key);

        const copy = document.createElement("script");

        for (const { name, value } of script.attributes) {
            copy.setAttribute(name, value);
        }

        copy.text = script.textContent ?? "";
        script.replaceWith(copy);
    }
}
