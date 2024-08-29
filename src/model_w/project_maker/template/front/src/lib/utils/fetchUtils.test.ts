/**
 * Tests for the fetch utilities.
 */
import { describe, it, expect, vi } from "vitest";
import { fetchWithErrorHandling } from "./fetchUtils.js";
import { error, isHttpError } from "@sveltejs/kit";

vi.mock("@sveltejs/kit", () => ({
    error: vi.fn(),
    isHttpError: vi.fn(),
}));

describe("fetchWithErrorHandling", () => {
    it("should return JSON data when the fetch is successful", async () => {
        const mockResponse = {
            ok: true,
            json: vi.fn().mockResolvedValue({ data: "test" }),
        };
        const fetchPromise = Promise.resolve(mockResponse as unknown as Response);

        const result = await fetchWithErrorHandling(fetchPromise);

        expect(result).toEqual({ data: "test" });
        expect(mockResponse.json).toHaveBeenCalled();
    });

    it("should call error with response status and body when response is not ok", async () => {
        const mockResponse = {
            ok: false,
            status: 404,
            json: vi.fn().mockResolvedValue({ error: "Not found" }),
        };
        const fetchPromise = Promise.resolve(mockResponse as unknown as Response);

        await fetchWithErrorHandling(fetchPromise);

        expect(error).toHaveBeenCalledWith(404, { error: "Not found" });
    });

    it("should handle network errors gracefully", async () => {
        const fetchPromise = Promise.reject(new Error("Network Error"));

        await fetchWithErrorHandling(fetchPromise);

        expect(error).toHaveBeenCalledWith(500, "Internal server error");
    });

    it("should handle HTTP errors gracefully", async () => {
        const mockHttpError = {
            status: 400,
            body: "Bad Request",
        };
        (isHttpError as unknown as vi.Mock).mockReturnValue(true);

        await fetchWithErrorHandling(Promise.reject(mockHttpError as any));

        expect(isHttpError).toHaveBeenCalledWith(mockHttpError);
        expect(error).toHaveBeenCalledWith(400, "Bad Request");
    });
});
