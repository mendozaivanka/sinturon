/**
 * Reads the same content from any JSON API or static host, e.g. a published release:
 *   DATA_SOURCE=http DATA_API_URL=https://mendozaivanka.github.io/sinturon/data/v1
 *
 *   GET {DATA_API_URL}/sinturon/records.json   (and cells-3deg, latitude, outliers, production, datasets, summary)
 *
 * If DATA_API_TOKEN is set it's sent as `Authorization: Bearer …`. Responses are validated like local data.
 */
import { DATA_API_URL, DATA_API_TOKEN } from "astro:env/server";
import type { DataSource } from "./types";

async function get(path: string): Promise<unknown> {
  if (!DATA_API_URL) throw new Error("DATA_SOURCE=http needs DATA_API_URL (see .env.example)");
  const url = `${DATA_API_URL.replace(/\/$/, "")}/${path}`;
  const res = await fetch(url, {
    headers: { Accept: "application/json", ...(DATA_API_TOKEN ? { Authorization: `Bearer ${DATA_API_TOKEN}` } : {}) },
  }).catch((e) => {
    throw new Error(`GET ${url} failed (${e.cause?.code ?? e.message}). Is DATA_API_URL right and the API up?`);
  });
  if (!res.ok) throw new Error(`GET ${url} → ${res.status} ${res.statusText}`);
  return res.json();
}

export const http: DataSource = {
  name: "http",
  sinturon: {
    records: () => get("sinturon/records.json"),
    cells: () => get("sinturon/cells-3deg.json"),
    latitude: () => get("sinturon/latitude.json"),
    outliers: () => get("sinturon/outliers.json"),
    production: () => get("sinturon/production.json"),
    datasets: () => get("sinturon/datasets.json"),
    summary: () => get("sinturon/summary.json"),
  },
};
