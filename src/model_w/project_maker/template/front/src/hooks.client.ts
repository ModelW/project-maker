import * as Sentry from "@sentry/sveltekit";
import { SENTRY_DSN, SENTRY_ENVIRONMENT } from "$app/env/public";

Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENVIRONMENT,
    tracesSampleRate: 1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1,
    // Needs the Document-Policy header set in hooks.server.ts
    profileSessionSampleRate: 1,
    profileLifecycle: "trace",
    integrations: [
        Sentry.replayIntegration(),
        Sentry.browserTracingIntegration({ enableInp: true }),
        Sentry.browserProfilingIntegration(),
    ],
});

export const handleError = Sentry.handleErrorWithSentry();
