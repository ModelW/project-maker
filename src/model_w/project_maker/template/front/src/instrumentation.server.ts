/**
 * Server-side Sentry initialization. SvelteKit runs this file before the
 * application code (see `kit.experimental.instrumentation` in
 * svelte.config.js), which is what lets the tracing and the Node profiler hook
 * into everything from the very start.
 */

import { nodeProfilingIntegration } from "@sentry/profiling-node";
import * as Sentry from "@sentry/sveltekit";
import { SENTRY_DSN, SENTRY_ENVIRONMENT } from "$app/env/public";

Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENVIRONMENT,
    tracesSampleRate: 1,
    profileSessionSampleRate: 1,
    profileLifecycle: "trace",
    integrations: [nodeProfilingIntegration()],
});
