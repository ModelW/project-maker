<template>
    <ServerTemplatedComponent
        :content="html as string"
        :components-defs="defs"
        @head="receiveHeadData"
    />
</template>

<script setup lang="ts">
import Title1 from "@/components/blocks/title-1.vue";
import { MetaObject } from "@nuxt/schema";
import type { NuxtError } from "#app";
import type { FetchResponse } from "ofetch";

const defs = {
    Title1,
};

const REDIRECT_CODE = [301, 302, 307, 308];

const html = ref<string>("<!DOCTYPE html><html lang='en'></html>");

/**
 * Just the raw HTTP query to get the response from Django. If we're on the
 * server, we're adding the appropriate headers so that the authentication and
 * other security measures can be passed along (which allows for previews to
 * work).
 */
async function fetchDjangoPage(): Promise<FetchResponse<string>> {
    const headers: Record<string, string> = {
        "X-Reach-API": "yes",
    };

    if (process.server) {
        const proxyHeaders = useRequestHeaders([
            "cookie",
            "origin",
            "referrer",
            "x-csrftoken",
        ]);
        Object.assign(headers, proxyHeaders);

        const hostCandidates = useRequestHeaders(["host", "x-forwarded-host"]);
        const host =
            hostCandidates["x-forwarded-host"] || hostCandidates["host"];

        if (host) {
            headers["X-Forwarded-Host"] = host;
        }
    }

    return await $fetch.raw(useRoute().fullPath, {
        baseURL: process.browser ? undefined : useNuxtApp().$config.apiUrl,
        headers,
        redirect: "manual",
    });
}

/**
 * Depending on the response, we'll either return the HTML to be used to render
 * the page or throw an error:
 *
 * - If it's a redirect, the error will have the status code of the redirect
 *   and contain a location in the data field. The goal is that the setup
 *   function can then navigate to that location.
 * - Otherwise it's any kind of error and we'll re-throw it from the setup
 *   function so that the error page is triggered.
 */
function decideResponseStrategy(resp: FetchResponse<string>) {
    if (200 <= resp.status && resp.status < 300) {
        const html = resp._data;

        if (html) {
            return {
                html,
            };
        } else {
            throw createError({
                statusCode: 500,
                message: "Empty response",
            });
        }
    } else if (REDIRECT_CODE.includes(resp.status)) {
        const location = resp.headers.get("location");

        if (location) {
            throw createError({
                statusCode: resp.status,
                message: "Redirect",
                data: { location },
            });
        } else {
            throw createError({
                statusCode: 500,
                message: "Invalid redirect",
            });
        }
    } else {
        throw createError({
            statusCode: resp.status,
            message: resp.statusText,
        });
    }
}

/**
 * This is in charge of getting the HTML from the server.
 *
 * Basically we're expecting a 200 status code. If that's the case, the
 * content should be HTML and we'll work with that.
 *
 * If not we try to figure out what is going on. If we've got a redirection
 * then we translate the redirection into Nuxt. Otherwise we just forward
 * the error. It's up to the implementer to handle errors 404, 500, etc.
 *
 * Let's note that those actions will be decided inside here but the action
 * will be taken from the setup function because Nuxt is made in a very logical
 * way apparently.
 *
 * Let's note that this works slightly different depending on if we're
 * running on the server side or the client side. Indeed, on the server
 * you'll have a `$config.apiUrl` value which allows to hit directly the
 * internal API URL, while on the client this value will be undefined and
 * we'll hit the URL relatively to the root path using the `x-reach-api`
 * header to tell the proxy to get this page from the API for us.
 */
async function getServerData() {
    const resp = await fetchDjangoPage();
    return decideResponseStrategy(resp);
}

const {
    /**
     * HTML from the server, if any
     */
    data,

    /**
     * Error that happened during async fetch, if any
     */
    error: fetchError,
} = await useAsyncData("html", getServerData);

if (fetchError.value) {
    const error = fetchError.value as any as Error | NuxtError;

    if ("statusCode" in error && REDIRECT_CODE.includes(error.statusCode)) {
        await navigateTo(error.data.location, {
            redirectCode: error.statusCode,
        });
    } else {
        throw error;
    }
}

if (
    typeof data.value === "object" &&
    data.value !== null &&
    "html" in data.value &&
    typeof data.value.html === "string"
) {
    html.value = data.value.html;
}

/**
 * Receiver for the head data from the parsed component, which allows to have
 * the proper meta info at SSR time.
 */
function receiveHeadData(head: MetaObject) {
    useHead(head);
}
</script>
