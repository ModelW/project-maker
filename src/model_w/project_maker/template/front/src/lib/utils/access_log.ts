/**
 * Module for logging access logs to the front server.
 *
 * Note: To keep consistency with the backend logs, we use the same author's
 *       plugin for getting the "real" IP.
 */
import pkg from "@fullerstack/nax-ipware";
import type { Handle } from "@sveltejs/kit";

const { Ipware } = pkg;
const ipware = new Ipware();

/**
 * Extracts the client's IP address from request headers.
 *
 * @param request The request object
 * @returns The IP address if found, or undefined if not found
 */
const getIpFromRequest = (request: Request) => {
    const ipInfo = ipware.getClientIP(request);

    return ipInfo?.ip ?? undefined;
};

/**
 * Middleware to log incoming requests and their responses.
 * Logs method, URL, response status, and execution time.
 *
 */
export const accessLog: Handle = async ({ event, resolve }) => {
    const start = Date.now();
    const { request } = event;
    const method = request.method;
    const url = request.url;

    const ip = getIpFromRequest(request) ?? event.getClientAddress();

    const userAgent = request.headers.get("user-agent");
    const response = await resolve(event);
    const duration = Date.now() - start;

    console.log(
        `[${new Date().toISOString()}] ${ip} "${method} - ${url}" ${response.status} (${duration}ms) "${userAgent}"`
    );

    return response;
};
