import { isRedirect } from "@sveltejs/kit";
import { describe, expect, it, vi } from "vitest";
import type { SessionProvider } from "$lib/session/provider";
import type { Me } from "$lib/session/types";
import { createMemorySessionCache, createMetaRouter, type RouteRule } from "./router";

const ANON: Me = { type: "anonymous" };
const USER: Me = { type: "authenticated", email: "a@b.c", firstName: "A", lastName: "B" };

function setup(rules: RouteRule[], me: Me = ANON) {
    const fetchMe = vi.fn(() => Promise.resolve(me));
    const sessionProvider: SessionProvider = {
        fetchMe,
        login: vi.fn(() => Promise.resolve(USER)),
        logout: vi.fn(() => Promise.resolve(ANON)),
    };
    const cache = createMemorySessionCache();
    const router = createMetaRouter({
        rules,
        sessionProvider,
        cache,
        loginUrl: (next) => `/login/?next=${next.pathname}`,
    });

    const resolve = (path: string) =>
        router.resolve({ url: new URL(path, "http://front"), fetch: globalThis.fetch });

    return { resolve, cache, fetchMe };
}

describe("createMetaRouter", () => {
    it("doesn't fetch the session for public routes", async () => {
        const { resolve, fetchMe } = setup([{ match: /^\/private/, requiresAuth: true }]);

        await expect(resolve("/public")).resolves.toEqual({ me: null });
        expect(fetchMe).not.toHaveBeenCalled();
    });

    it("redirects anonymous visitors away from protected routes", async () => {
        const { resolve } = setup([{ match: /^\/private/, requiresAuth: true }]);

        const error = await resolve("/private/page").catch((e: unknown) => e);

        expect(isRedirect(error)).toBe(true);
        expect(isRedirect(error) && error.location).toBe("/login/?next=/private/page");
    });

    it("lets authenticated visitors in and remembers them", async () => {
        const { resolve, fetchMe } = setup([{ match: /^\/private/, requiresAuth: true }], USER);

        await expect(resolve("/private/a")).resolves.toEqual({ me: USER });
        await expect(resolve("/private/b")).resolves.toEqual({ me: USER });
        expect(fetchMe).toHaveBeenCalledTimes(1);
    });

    it("refetches the session on each visit when asked to", async () => {
        const { resolve, fetchMe } = setup([{ match: /^\/fresh/, refreshSession: true }], USER);

        await resolve("/fresh");
        await resolve("/fresh");
        expect(fetchMe).toHaveBeenCalledTimes(2);
    });

    it("refetches the session once after a refresh request", async () => {
        const { resolve, cache, fetchMe } = setup([]);

        cache.requestRefresh();
        await expect(resolve("/public")).resolves.toEqual({ me: ANON });
        await resolve("/public");
        expect(fetchMe).toHaveBeenCalledTimes(1);
    });

    it("applies the first matching rule, including function matchers", async () => {
        const { resolve, fetchMe } = setup([
            { match: (url) => url.searchParams.has("public") },
            { match: /.*/, requiresAuth: true },
        ]);

        await expect(resolve("/anything?public")).resolves.toEqual({ me: null });
        expect(fetchMe).not.toHaveBeenCalled();
    });
});
