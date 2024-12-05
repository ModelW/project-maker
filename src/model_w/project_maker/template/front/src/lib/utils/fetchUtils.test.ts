/**
 * Tests for the fetch utilities.
 */
import { describe, it, expect, vi, type Mock, beforeEach } from "vitest";
import { fetchWithErrorHandling } from "./fetchUtils";
import { error, isHttpError, isRedirect, redirect } from "@sveltejs/kit";

vi.mock("@sveltejs/kit", () => ({
    error: vi.fn() as Mock<[number, string?], void>,
    isHttpError: vi.fn() as Mock<[unknown], boolean>,
    isRedirect: vi.fn() as Mock<[unknown], boolean>,
    redirect: vi.fn() as Mock<[number, string], void>,
}));

describe("fetchWithErrorHandling", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should return parsed JSON for a successful response", async () => {
        const mockResponse = {
            ok: true,
            headers: new Map(),
            json: vi.fn().mockResolvedValue({ success: true }),
        } as unknown as Response;

        const result = await fetchWithErrorHandling(Promise.resolve(mockResponse));
        expect(result).toEqual({ success: true });
        expect(error).not.toHaveBeenCalled();
        expect(redirect).not.toHaveBeenCalled();
    });

    it("should handle HTTP errors gracefully", async () => {
        const mockHttpError = { status: 400, body: "Bad Request" };

        (isHttpError as unknown as Mock).mockReturnValue(true);
        await fetchWithErrorHandling(Promise.reject(mockHttpError));

        expect(isHttpError).toHaveBeenCalledWith(mockHttpError);
        expect(error).toHaveBeenCalledWith(400, "Bad Request");
    });

    it("should handle API HTTP errors returned from the promise", async () => {
        const mockError = { status: 500, body: "Internal Server Error" };

        (isHttpError as unknown as Mock).mockReturnValue(true);
        await fetchWithErrorHandling(Promise.reject(mockError));

        expect(isHttpError).toHaveBeenCalledWith(mockError);
        expect(error).toHaveBeenCalledWith(500, "Internal Server Error");
    });

    it("should handle unknown errors with a generic message", async () => {
        const unknownError = new Error("Unexpected failure");

        (isHttpError as unknown as Mock).mockReturnValue(false);
        (isRedirect as unknown as Mock).mockReturnValue(false);

        await fetchWithErrorHandling(Promise.reject(unknownError));

        expect(isHttpError).toHaveBeenCalledWith(unknownError);
        expect(isRedirect).toHaveBeenCalledWith(unknownError);
        expect(error).toHaveBeenCalledWith(500, "Internal server error");
    });

    it("should handle redirects thrown as exceptions", async () => {
        const redirectError = { status: 302, location: "https://example.com" };

        (isRedirect as unknown as Mock).mockReturnValue(true);
        await fetchWithErrorHandling(Promise.reject(redirectError));

        expect(isRedirect).toHaveBeenCalledWith(redirectError);
        expect(redirect).toHaveBeenCalledWith(302, "https://example.com");
    });

    it("should handle permanent redirects from API response headers", async () => {
        const mockResponse = {
            status: 301,
            headers: new Map([["X-Redirect-To", "https://example.com/custom-redirect"]]),
            json: vi.fn().mockResolvedValue({}),
        } as unknown as Response;

        await fetchWithErrorHandling(Promise.resolve(mockResponse));

        expect(redirect).toHaveBeenCalledWith(301, "https://example.com/custom-redirect");
        expect(error).not.toHaveBeenCalled();
    });

    it("should handle temporary redirects from API response headers", async () => {
        const mockResponse = {
            status: 302,
            headers: new Map([["X-Redirect-To", "https://example.com"]]),
            json: vi.fn().mockResolvedValue({}),
        } as unknown as Response;

        await fetchWithErrorHandling(Promise.resolve(mockResponse));

        expect(redirect).toHaveBeenCalledWith(302, "https://example.com");
        expect(error).not.toHaveBeenCalled();
    });
});
