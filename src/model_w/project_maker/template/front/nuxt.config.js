import { resolve } from "node:path";
import { envManager, defineModelWConfig } from "@model-w/preset-nuxt3";

const config = envManager((env) => {
    return defineModelWConfig(env, {
        siteName: "___project_name__snake___",
        head: {
            meta: [
                { charset: "utf-8" },
                {
                    name: "viewport",
                    content: "width=device-width, initial-scale=1",
                },
                { name: "format-detection", content: "telephone=no" },
            ],
        },
    });
});

config.vite = {
    resolve: {
        alias: {
            vue: resolve(__dirname, "node_modules/vue/dist/vue.esm-bundler.js"),
        },
    },
};

export default config;
