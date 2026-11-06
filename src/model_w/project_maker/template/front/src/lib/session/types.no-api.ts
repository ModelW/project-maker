/**
 * Types of the user's session, for projects without the Model W API. Replaces
 * `types.ts` at generation time. Adapt them to your own authentication
 * backend, but keep the `type` field which tells both cases apart.
 */

/** The visitor is logged in */
export interface AuthUser {
    type: "authenticated";
    email: string;
    firstName: string;
    lastName: string;
}

/** The visitor is not logged in */
export interface AnonUser {
    type: "anonymous";
}

/** The session: authenticated or anonymous */
export type Me = AuthUser | AnonUser;

/** What `login()` expects */
export interface Credentials {
    email: string;
    password: string;
}
