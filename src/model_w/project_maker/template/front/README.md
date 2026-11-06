# Front

This is a SvelteKit application serving all the front-end pages.

## Commands

| Command       | What it does                                |
| ------------- | ------------------------------------------- |
| `pnpm dev`    | Development server on http://localhost:3000 |
| `pnpm build`  | Production build                            |
| `pnpm lint`   | Prettier check + ESLint (the CI runs both)  |
| `pnpm check`  | Type checking with svelte-check             |
| `pnpm test`   | Unit tests with Vitest                      |
| `pnpm format` | Formats everything with Prettier            |

## Environment variables

All the variables the app reads are declared in `src/env.ts` and validated with
[Valibot](https://valibot.dev/) when the app starts: if one is missing or
invalid, the app refuses to start. They are only optional while building.

# :: IF api__enable

- `API_URL` (private) &mdash; Where the front's server reaches the API, also
  the target of the dev proxy

# :: ENDIF

- `SENTRY_DSN` (public) &mdash; Sentry DSN, empty to disable error reporting
  (optional in development)
- `SENTRY_ENVIRONMENT` (public) &mdash; Name of the environment in Sentry
  (optional in development)

Import them from `$app/env/private` (server-only code) or `$app/env/public`.
To add one, declare it in `src/env.ts` first.

The Sentry source maps upload uses `SENTRY_ORG`, `SENTRY_PROJECT`, `SENTRY_URL`
and `SENTRY_AUTH_TOKEN`, only at build time (see `vite.config.ts`).

## Layout

The routes are split in groups:

| Group        | What's inside                                                         |
| ------------ | --------------------------------------------------------------------- |
| `routes/`    | Root layout: global styles (`$lib/styles/main.scss`) and contexts     |
| `(site)/`    | Pages of the site, with the header, the footer and the main container |
| `(preview)/` | Previews rendered inside the CMS, without the header and footer       |

The header (`$lib/components/layout/Header.svelte`) is fixed and shrinks as the
page scrolls, using a CSS scroll-driven animation (no JavaScript). Browsers
without support for it (and visitors who prefer reduced motion) get a header
that doesn't shrink. On small screens the navigation moves into a drawer
([svaul](https://github.com/harshmandan/svaul)) opened by a burger button.

Global CSS variables (fonts, header height, breakpoints) are defined in
`$lib/styles/base/`. Use the `.container` class to center content.

## Menus

The content of the header and the footer comes from `$lib/navigation/menus.ts`.
An entry is either a link (`label` and `href`) or a group (`label` and
`children`), shown as a dropdown in the header and as a column in the footer.
The functions in there are async and receive SvelteKit's `fetch`, so that the
day the menus come from the CMS, only their body needs to change.

They are loaded once by the root layout and available anywhere:

```svelte
<script lang="ts">
    import { useMenu } from "$lib/navigation/context";
    import { isMenuGroup } from "$lib/navigation/menus";

    const menu = useMenu("header");
</script>

{#each menu.items as item (item.label)}
    {#if isMenuGroup(item)}
        <span>{item.label}</span> <!-- then item.children -->
    {:else}
        <a href={item.href}>{item.label}</a>
    {/if}
{/each}
```

# :: IF api__enable

## API client

The front only talks to the API through the client in `$lib/api`, which is
generated from the API's OpenAPI schema (`src/lib/api/client/`, never edit it
by hand):

```ts
import { createApiClient } from "$lib/api";

// In a load function, pass SvelteKit's fetch
const me = await createApiClient(fetch).me.whoami();
```

Whenever an endpoint or a schema of the API changes, regenerate it and commit
the result:

```bash
cd api && make ts_client
```

The method names come from the `operation_id` of the Ninja endpoints, so give
each endpoint an explicit one.

# :: ENDIF

## Session and route rules

The visitor's session (the API's `GET /back/api/me/`) is available anywhere.
Its `type` is either `"authenticated"` or `"anonymous"`, and checking it
narrows the type:

```svelte
<script lang="ts">
    import { useSession } from "$lib/session/context";

    const session = useSession();
</script>

{#if session.me?.type === "authenticated"}
    Hello {session.me.firstName}
{/if}
```

The session is only fetched when needed. Which routes need it is decided by
the rules of the meta router, in `$lib/meta-router/config.ts`:

```ts
export const routeRules: RouteRule[] = [
    // Anonymous visitors get sent to loginUrl()
    { match: /^\/account(\/|$)/, requiresAuth: true },

    // The session is fetched again each time the visitor gets there
    { match: /^\/checkout(\/|$)/, refreshSession: true },
];
```

- The first matching rule wins, URLs matching no rule are public and don't
  touch the session. In that case `session.me` is `null`, which means
  "unknown" (call `session.refresh()` if you need to know anyway).
- Once the visitor is known to be logged in, the session is remembered in
  the browser and protected pages don't fetch it again.
- `loginUrl()`, in the same file, is where anonymous visitors are sent.
- `useSession()` also provides `refresh()`, `login()` and `logout()`, which
  update the session and re-apply the rules.

This is about user experience, the API remains in charge of security.

# :: IF api__wagtail

## CMS

CMS pages are rendered by the catch-all route `(site)/(cms)/[...cmsPath]`,
which picks the page component from the page type (see the API's README for
the naming conventions). StreamField blocks are rendered by the
`StreamField` component, which finds the component of each block by its name
in `$lib/components/cms/blocks/`.

Page, block and snippet previews require the visitor to be logged in, as
declared in the meta router's rules.

# :: ENDIF
