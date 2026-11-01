// @ts-check
import { defineConfig, envField } from "astro/config";
import { loadEnv } from "vite";
import react from "@astrojs/react";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

// Sinturon is a GitHub Pages *project site*: it is served at https://mendozaivanka.github.io/sinturon/, beside the
// portfolio at the root of the same domain. Every option can be overridden in the environment (.env.example).
const env = loadEnv(process.env.NODE_ENV ?? "production", process.cwd(), "");

export default defineConfig({
  site: env.SITE_URL || "https://mendozaivanka.github.io",
  base: env.BASE_PATH || "/sinturon",
  output: "static",
  // Directory URLs (/sinturon/map/) are how GitHub Pages serves folders.
  trailingSlash: "always",
  integrations: [react(), sitemap()],
  env: {
    schema: {
      DATA_SOURCE: envField.enum({ context: "server", access: "public", values: ["local", "http"], default: "local" }),
      DATA_API_URL: envField.string({ context: "server", access: "public", optional: true, url: true }),
      DATA_API_TOKEN: envField.string({ context: "server", access: "secret", optional: true }),
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
