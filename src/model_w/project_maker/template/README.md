# ~~~project_title~~~

It's up to you to write the description of the project. If you just cloned this
repo and see this it means you can `git blame` the README and go explain to the
person who committed this that it's mandatory to write documentation 😇

## Installation & Usage

This project is built upon [Model W](https://model-w.rtfd.io/). Hence, all
conventions apply.

In particular this was created using the
[Project Maker](https://github.com/ModelW/project-maker).

> **Note** &mdash; Don't forget to read the part about
> [Django Models Customization](https://github.com/modelw/project-maker#django-models-customization).

## Documentation

The documentation of this project follows the
[Code Guidelines](https://with-codeguidelines.readthedocs-hosted.com/en/latest/documentation.html)
from WITH.

### Components

This project is composed of the following components:
# :: IF api__enable
-   [API](./api) &mdash; The back-end of the project, mostly serving as API and
    back-office admin. Most of the time, URLs targeting the API are prefixed by
    `/back`.
# :: ENDIF
# :: IF front__enable
-   [Front](./front) &mdash; The front-end, which renders all the
    customer-facing pages. It covers the rest of URLs.
# :: ENDIF

### One origin for everything

The API and the front-end are served from the same domain, which avoids CORS
altogether and lets them share cookies (sessions, CSRF):

-   Everything under `/back/` goes to the API
-   Everything else goes to the front-end

In production, that's the job of the load balancer, which routes according to
the URL. In development, it's the proxy embedded in Vite (see
`front/vite.config.ts`). In the E2E tests, a router container mimics the load
balancer (`api/bdd/_infrastructure/mock-digital-ocean-router.conf`).

`BASE_URL` (API side) is the public URL of the site, so the one of that single
origin. The only time the API is reached directly is when the front-end's
server talks to it, through `API_URL` (front side).

### Deployment

The deployment is described in [`snow.yml`](./snow.yml): images, components,
routing, resources and the environment variables of each component. Values
come from the deployment itself (database, URLs, environment name), or from
the variables and secrets to set for each environment:

| Name                      | Kind   | Purpose                                    |
| ------------------------- | ------ | ------------------------------------------ |
# :: IF api__enable
| `SECRET_KEY`              | secret | Django's secret key                        |
| `API_SENTRY_DSN`          | var    | Sentry DSN of the API (empty to disable)   |
# :: ENDIF
# :: IF api__wagtail
| `DO_REGION`               | var    | Region of the media bucket (e.g. `ams3`)   |
| `AWS_ACCESS_KEY_ID`       | var    | Access key of the media bucket             |
| `AWS_SECRET_ACCESS_KEY`   | secret | Secret key of the media bucket             |
| `AWS_STORAGE_BUCKET_NAME` | var    | Name of the media bucket                   |
| `AWS_S3_CUSTOM_DOMAIN`    | var    | Public domain of the media bucket          |
# :: ENDIF
# :: IF front__enable
| `FRONT_SENTRY_DSN`        | var    | Sentry DSN of the front (empty to disable) |
| `SENTRY_AUTH_TOKEN`       | secret | Uploads the front's source maps to Sentry  |
| `SENTRY_ORG`              | var    | Sentry organization (source maps)          |
| `FRONT_SENTRY_PROJECT`    | var    | Sentry project of the front (source maps)  |
| `SENTRY_URL`              | var    | Sentry instance URL (source maps)          |
# :: ENDIF

### Writing more of it

If you feel like the Model W documentation is not enough:

-   If it's a generic problem, open a PR to Model W documentation so that all
    Model W users can benefit from your improvements in the documentation.
-   If not feel free to directly change the documentation of your project.
