FROM modelw/base:2024.07

COPY --chown=user package.json package-lock.json ./

RUN modelw-docker install

COPY --chown=user . .

RUN modelw-docker build

CMD ["modelw-docker", "serve"]
