/**
 * Environment variables of the front, validated when the app starts: a
 * missing or invalid variable makes it crash right away instead of failing
 * later in a confusing way. They can then be imported from
 * `$app/env/private` (server only) or `$app/env/public` (also sent to the
 * browser).
 *
 * Variables are only optional while building (see `required()`), which is
 * the equivalent of the API's `BUILD_MODE`.
 *
 * Build-time-only variables (Sentry source maps upload) are read in
 * `vite.config.ts`, not here.
 *
 * See https://svelte.dev/docs/kit/environment-variables
 */

import { defineEnvVars } from "@sveltejs/kit/env";
import { building } from "$app/env";
import * as v from "valibot";

/**
 * Makes a variable mandatory when the app runs, but optional while it's being
 * built (when the actual environment isn't known yet).
 *
 * @param schema Validation of the variable when it is defined
 */
function required<T extends v.GenericSchema<string>>(schema: T): T {
    // The variables are typed as when the app runs, as it's the only moment
    // they are read
    return building ? (v.optional(schema) as unknown as T) : schema;
}

export const variables = defineEnvVars({
    // :: IF api__enable
    API_URL: {
        description:
            "Where the server side of the front can reach the API (also the target of the dev proxy)",
        schema: required(v.pipe(v.string(), v.url())),
    },
    // :: ENDIF
    SENTRY_DSN: {
        public: true,
        description: "DSN of the Sentry project, empty to disable error reporting",
        schema: required(v.string()),
    },
    SENTRY_ENVIRONMENT: {
        public: true,
        description: "Name of the environment in Sentry (e.g. production, staging)",
        schema: required(v.string()),
    },
});
