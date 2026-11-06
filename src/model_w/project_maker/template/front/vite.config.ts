import { sveltekit } from "@sveltejs/kit/vite";
import { sentrySvelteKit } from "@sentry/sveltekit/vite";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
    // Empty prefix: read all variables, not only the VITE_ ones
    const env = loadEnv(mode, process.cwd(), "");

    return {
        plugins: [
            sentrySvelteKit({
                // Only needed at build time, to upload the source maps
                org: env.SENTRY_ORG,
                project: env.SENTRY_PROJECT,
                sentryUrl: env.SENTRY_URL,
                authToken: env.SENTRY_AUTH_TOKEN,
                sourcemaps: {
                    assets: ["./build/*/**/*"],
                    filesToDeleteAfterUpload: ["./build/**/*.map"],
                },
            }),
            sveltekit(),
        ],
        test: {
            include: ["src/**/*.{test,spec}.{js,ts}"],
        },
        // :: IF api__enable
        server: {
            proxy: {
                "/back": { target: env.API_URL },
            },
        },
        // :: ENDIF
        build: {
            target: "es2017",
        },
    };
});
