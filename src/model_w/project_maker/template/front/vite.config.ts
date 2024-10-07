import { sveltekit } from "@sveltejs/kit/vite";
import { sentrySvelteKit } from "@sentry/sveltekit";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd());

    return {
        plugins: [
            sveltekit(),
            sentrySvelteKit({
                sourceMapsUploadOptions: {
                    org: env.PUBLIC_SENTRY_ORG,
                    project: env.PUBLIC_SENTRY_PROJECT,
                    url: env.PUBLIC_SENTRY_URL,
                    authToken: process.env.SENTRY_AUTH_TOKEN,
                    sourcemaps: {
                        assets: ["./build/*/**/*"],
                        filesToDeleteAfterUpload: ["./build/**/*.map"],
                    },
                },
            }),
        ],
        test: {
            include: ["src/**/*.{test,spec}.{js,ts}"],
        },
        server: {
            proxy: {
                "/back": { target: env.VITE_API_URL },
            },
        },
        build: {
            target: "es2017",
        },
    };
});
