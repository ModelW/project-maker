import * as Sentry from "@sentry/sveltekit";
import { SENTRY_DSN, SENTRY_ENVIRONMENT } from "$app/env/public";

Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENVIRONMENT,
    tracesSampleRate: 1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1,
    integrations: [
        Sentry.replayIntegration(),
        Sentry.browserTracingIntegration({ enableInp: true }),
    ],
});

export const handleError = Sentry.handleErrorWithSentry();
