import {defineModelWConfig} from "@model-w/preset-nuxt3";

/**
 * Modifies the request from the proxy in order to make sure that Django behind
 * the request can interpret the correct host from X-Forwarded-Host instead of
 * using the host it receives which is the internal host name from the DO PaaS
 * (or any other internal name on another Kubernetes-like platform).
 */
function addForwardedHost(proxyReq: any, req: any) {
    const host = req.headers["x-forwarded-host"] || req.headers.host;

    if (host) {
        proxyReq.setHeader("x-forwarded-host", host);
    }
}

export default (
    defineModelWConfig({
            siteName: process.env.SITE_NAME,
            apiURL: process.env.API_URL,
            sentryDSN: process.env.SENTRY_DSN,
            ENV: process.env.ENV,
            meta: [
                    { charset: "utf-8" },
                    {
                        name: "viewport",
                        content: "width=device-width, initial-scale=1",
                    },
                    { hid: "description", name: "description", content: "" },
                    { name: "format-detection", content: "telephone=no" },
                ],
            backAlias: process.env.BACK_ALIAS,
            cmsAlias: process.env.CMS_ALIAS,
            moduleConfig: [
            ],
        }
    )
);
