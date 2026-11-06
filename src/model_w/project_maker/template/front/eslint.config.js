/**
 * ESLint flat config for the SvelteKit front.
 *
 * Layers: JS recommended → TS recommended (+type-checked) → Svelte
 * recommended → prettier last so formatting stays Prettier's job.
 */
import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import ts from "typescript-eslint";

/** @type {import('eslint').Linter.Config[]} */
export default [
    js.configs.recommended,
    ...ts.configs.recommended,
    ...svelte.configs["flat/recommended"],
    prettier,
    ...svelte.configs["flat/prettier"],
    {
        rules: {
            curly: "error",

            // Unused arguments are fine as long as they say so
            "@typescript-eslint/no-unused-vars": [
                "error",
                { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
            ],

            /**
             * Links mostly point to URLs that come from the CMS, the API or
             * the menus (including `/back/` URLs that SvelteKit doesn't
             * route), which can't go through resolve(). Programmatic
             * navigation (goto) is still checked.
             */
            "svelte/no-navigation-without-resolve": ["error", { ignoreLinks: true }],
        },
    },
    {
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.node,
            },
        },
    },
    // Type-aware linting for TS and Svelte files. Plain .js config files
    // (eslint.config.js, svelte.config.js) are deliberately excluded: their
    // membership in the project service depends on whether svelte-kit sync
    // has run, which makes the config flaky between local and CI.
    {
        files: ["**/*.ts", "**/*.svelte"],
        languageOptions: {
            parserOptions: {
                projectService: true,
                tsconfigRootDir: import.meta.dirname,
                extraFileExtensions: [".svelte"],
            },
        },
    },
    ...ts.configs.recommendedTypeChecked.map((config) => ({
        ...config,
        files: ["**/*.ts"],
    })),
    {
        files: ["**/*.svelte"],
        languageOptions: {
            parserOptions: {
                parser: ts.parser,
            },
        },
        rules: {
            ...ts.configs.recommendedTypeChecked.reduce(
                (acc, config) => ({ ...acc, ...config.rules }),
                {}
            ),
            "prefer-const": "off",
        },
    },
    {
        rules: {
            // SvelteKit's error() and redirect() throw non-Error objects by design
            "@typescript-eslint/only-throw-error": "off",

            /**
             * The "no unsafe" family is counter-productive here: the CMS page
             * and block rendering is meta-programmed (dynamic component
             * resolution from API data), so a lot of typing info is unknown
             * at compile time by definition.
             */
            "@typescript-eslint/no-unsafe-member-access": "off",
            "@typescript-eslint/no-unsafe-assignment": "off",
            "@typescript-eslint/no-explicit-any": "off",
            "@typescript-eslint/no-unsafe-call": "off",
            "@typescript-eslint/no-unsafe-argument": "off",
            "@typescript-eslint/no-unsafe-return": "off",
        },
    },
    {
        files: ["**/*.test.ts"],
        rules: {
            /**
             * SvelteKit's error()/redirect() throw plain objects by design;
             * tests reject with the same shapes to mirror runtime behavior.
             */
            "@typescript-eslint/prefer-promise-reject-errors": "off",
        },
    },
    {
        // The API client is generated (see src/lib/api/index.ts)
        ignores: ["build/", ".svelte-kit/", "dist/", "src/lib/api/client/"],
    },
];
