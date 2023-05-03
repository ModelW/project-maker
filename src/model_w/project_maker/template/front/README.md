# Front

This is a Nuxt application serving all the front-end pages.

## Communication with API

It is recommended to call the API directly through the `$axios` instance
provided by Nuxt, using an absolute URL without the domain name. For example if
you want to know the user's current authentication status:

```js
const user = await $axios.$get("/back/api/me/");
```

Doing so will make sure that the call works both on server-side and client-side
(as we're working with a SSR app here).

# :: IF api~~wagtail

## Wagtail

The content pages are served by Wagtail on the Django side. This behavior is
handled by the [catch-all page](./pages/[...wagtail].vue) which will:

1. Call the Wagtail API for the page we're trying to get
2. If there is any error (404, 500, ...) the error will be rendered as a Nuxt
   error. The same goes with redirections.
3. If the page is found, it will be rendered using the
   [`ServerTemplatedComponent`](./components/ServerTemplatedComponent.vue)
   component. It lets you declare Vue components that have their JS and CSS
   (non-scoped) declared in a `.vue` file but the template coming from the
   server.

In order to render more components through the `ServerTemplatedComponent`, you
must:

1. Create the component itself (wherever you want), without defining a template
2. In the component's default, add a `selector` property that will be used to
   find in the server-generated HTML the location(s) where this component needs
   to be inserted.
3. Add this component to [`[...wagtail].vue`](./pages/[...wagtail].vue) in the `DEFS` constants.

# :: ENDIF
