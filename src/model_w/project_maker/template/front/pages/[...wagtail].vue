<template>
    <ServerTemplatedComponent
        :content="html"
        :components-defs="defs"
        @head="receiveHeadData"
    />
</template>

<script>
import { defineNuxtComponent } from "nuxt/app";
import ServerTemplatedComponent from "~/components/ServerTemplatedComponent.vue";
import Title1 from "~/components/blocks/Title1.vue";

/**
 * Put here all the components that you might want to render
 */
const DEFS = {
    Title1,
};

/**
 * This is the "fall-back" page which will try to fetch and render a page from
 * the underlying Wagtail hosted in the API. Everything here is a sane default,
 * however you might want to customize it depending on your use.
 *
 * The thing you'll want to customize the most is most likely the defs list!
 */
export default defineNuxtComponent({
    components: {
        ServerTemplatedComponent,
    },

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
     * Let's note that this works slightly different depending on if we're
     * running on the server side or the client side. Indeed, on the server
     * you'll have a `$config.apiUrl` value which allows to hit directly the
     * internal API URL, while on the client this value will be undefined and
     * we'll hit the URL relatively to the root path using the `x-reach-api`
     * header to tell the proxy to get this page from the API for us.
     */
    async asyncData({ $axios, $config, $router, ssrContext }) {
        async function getAsyncData($axios, baseURL, path, query) {
            try {
                const headers = ssrContext?.event.node.req.headers ?? {};
                headers["x-reach-api"] = "yes";
                return {
                    html: await $axios.$get(path, {
                        baseURL,
                        headers,
                        maxRedirects: 0,
                        params: query,
                        validateStatus(status) {
                            return status === 200;
                        },
                    }),
                };
            } catch (e) {
                const { response: res } = e;

                if (res) {
                    const isRedirect = [301, 302, 307, 308].includes(
                        res.status
                    );
                    const location = res.headers.location;

                    if (isRedirect) {
                        if (location) {
                            return await getAsyncData(
                                $axios,
                                baseURL,
                                location,
                                query
                            );
                        } else {
                            // $sentry.captureException(e);
                            return createError({
                                statusCode: res.status,
                                message: "Invalid redirect",
                            });
                        }
                    } else {
                        // $sentry.captureException(e);
                        return createError({
                            statusCode: res.status,
                            message: res.statusText,
                        });
                    }
                } else {
                    // $sentry.captureException(e);
                    // eslint-disable-next-line
                    console.error(e);
                    return createError({
                        statusCode: 500,
                        message: "Unknown error",
                    });
                }
            }
        }

        const route = $router.currentRoute.value;
        return await getAsyncData(
            $axios,
            process.browser ? undefined : $config.apiUrl,
            route.path,
            route.query
        );
    },

    data() {
        return {
            /**
             * HTML code of the page
             */
            html: "",

            /**
             * Head data extracted from the template's head
             */
            headData: {},
        };
    },

    /**
     * Propagates the head data from the template into Nuxt's head system
     */
    head() {
        return this.headData ?? {};
    },

    computed: {
        /**
         * Exposes the defs
         */
        defs() {
            return DEFS;
        },

        /**
         * Whether the page is a draft
         */
        isPreview() {
            return this.$route.path.replace(/^\/$/, "").endsWith("/preview");
        },
    },

    methods: {
        /**
         * This serves to receive updates about the head data extracted by
         * ServerTemplatedComponent
         */
        receiveHeadData(head) {
            this.headData = head;
        },
    },
});
</script>
