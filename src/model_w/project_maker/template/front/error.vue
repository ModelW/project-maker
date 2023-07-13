<!--
This is the catch-all page for errors of all sorts, either 404s or 500s that
come either from internal malfunction of Nuxt or from Django. So the strategy
here is: implement the special cases that you want handled cleanly (like 404s)
and then make sure it's always more or less decent for all other kinds of weird
errors.
-->

<template>
    <!-- For implementer: manage your different cases here -->
    <div class="error">
        <h1>{{ errorTitle }}</h1>
    </div>

    <!-- In dev mode, we want to be able to see the stack trace -->
    <DevOnly>
        <div v-if="error.stack && stackIsOpen" class="dev-error">
            <div class="message">
                {{ error.message }}
                <button @click="closeStack">(close)</button>
                <button @click="reload">(reload page)</button>
            </div>
            <div class="stack-container" v-html="error.stack"></div>
        </div>
    </DevOnly>
</template>

<style lang="scss" scoped>
$margin: 20px;

/**
 * A little floating box for the exceptions in dev mode.
 */
.dev-error {
    position: absolute;
    box-sizing: border-box;
    top: $margin;
    right: $margin;
    padding: 15px;
    max-width: calc(100vw - $margin * 2);
    color: white;
    background: rgba(80, 46, 46, 0.9);
}

/**
 * Custom style for the exception's message
 */
.message {
    font-size: 20px;
    font-family: sans-serif;
}

/**
 * We want the stack trace to be scrollable in case it's too wide
 */
.stack-container {
    overflow: auto;
}

/**
 * Convenience buttons, we just remove the default button style here
 */
button {
    font-size: 18px;
    font-family: sans-serif;
    display: inline-block;
    margin: 0 0 0 10px;
    padding: 0;
    border: 0;
    background: transparent;
    color: rgba(255, 255, 255, 0.85);
    text-decoration: underline;
}
</style>

<script setup lang="ts">
import type { Ref } from "vue";
import type { NuxtError } from "#app";

/**
 * The current error, either a NuxtError or at least some JS exception. We'll
 * make the best of it later.
 */
const error = useError() as Ref<Error | NuxtError>;

/**
 * If we're in dev mode, indicates if the stack is open.
 */
const stackIsOpen = ref(true);

/**
 * We compute here the title of the error. Fundamentally this will probably
 * go away when you implement nicer error pages, however it kinds of shows
 * the idea of how to get the error safely and in a way that TS doesn't
 * complain about.
 */
const errorTitle = computed(() => {
    const ev = error.value;

    if ("statusCode" in ev) {
        return `${ev.statusCode} ${ev.statusMessage || "Internal Error"}`;
    }

    return "Unknown error";
});

/**
 * Closes the stack trace in dev mode.
 */
function closeStack() {
    stackIsOpen.value = false;
}

/**
 * Reloads the page.
 */
function reload() {
    window.location.reload();
}

watchEffect(() => {
    useHead({
        title: errorTitle.value,
    });
});
</script>
