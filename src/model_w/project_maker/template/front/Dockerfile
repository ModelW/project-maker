FROM modelw/base:2026.10

COPY --chown=user .npmrc package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN modelw-docker install

COPY --chown=user . .

# Sentry source maps upload (see vite.config.ts), passed by the deployment
# (the "sentry-build" envs of snow.yml). Without them, nothing is uploaded.
ARG SENTRY_AUTH_TOKEN
ARG SENTRY_ORG
ARG SENTRY_PROJECT
ARG SENTRY_URL

RUN modelw-docker build

CMD [ "modelw-docker", "serve" ]
