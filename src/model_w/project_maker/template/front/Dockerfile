FROM modelw/base:2026.10

COPY --chown=user .npmrc package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN modelw-docker install

COPY --chown=user . .

RUN modelw-docker build

CMD [ "modelw-docker", "serve" ]
