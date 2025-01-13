FROM modelw/base:2025.01

COPY --chown=user .npmrc package.json package-lock.json ./

RUN modelw-docker install

COPY --chown=user . .

RUN modelw-docker build

CMD [ "modelw-docker", "serve" ]
