FROM modelw/base:2024.10

COPY --chown=user .npmrc package.json package-lock.json ./

RUN modelw-docker install

COPY --chown=user . .

RUN modelw-docker build \
    && npm prune --omit dev

ARG PORT=3000
ENV PORT=${PORT:-3000}
EXPOSE ${PORT}

ENV NODE_ENV=production

CMD [ "node", "./build/index.js" ]
