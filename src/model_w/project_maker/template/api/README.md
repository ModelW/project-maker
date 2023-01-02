# API

This handles the API and back-office admin.

All the URLs pointing to this are prefixed by `/back`.

# :: IF api~~wagtail

> **Note** &mdash; There is one exception to this, which is the Wagtail previous
> system. They are fairly complex, and it's the proxy middleware in Nuxt taking
> care of this. Check [`*.vue`](../front/pages/*.vue) and
> [`nuxt.config.js`](../front/nuxt.config.js) for more info.

# :: ENDIF

## Components

You'll find the following apps:

-   [people](./___project_name__snake___/apps/people) &mdash; The user model and
    authentication.

# :: IF api~~channels

-   [realtime](./___project_name__snake___/apps/realtime) &mdash; Deals with
    websockets

# :: ENDIF

# :: IF api~~wagtail

-   [cms](./___project_name__snake___/apps/cms) &mdash; All the page models for
    Wagtail

# :: ENDIF

## OpenAPI

When the app is in development mode, you can access the OpenAPI documentation at
`/back/api/schema/redoc/`.

This documentation is auto-generated using
[drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/). As you
create more APIs, make sure that they render nicely in OpenAPI format.
