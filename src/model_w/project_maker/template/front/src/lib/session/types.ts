/**
 * Types of the user's session. They come from the API client, generated from
 * the schemas of the API's "me" endpoints.
 *
 * `type` tells both cases apart: `me.type === "authenticated"` narrows `me`
 * to the authenticated user.
 */

export type {
    /** The visitor is not logged in */
    AnonUserOut as AnonUser,
    /** The visitor is logged in */
    AuthUserOut as AuthUser,
    /** What `login()` expects */
    AuthUserIn as Credentials,
    /** The session: authenticated or anonymous */
    Me,
} from "$lib/api";
