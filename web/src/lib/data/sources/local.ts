/**
 * The default source: the JSON in src/data/sinturon/, unpacked from the pinned data release by
 * `npm run data:pull` (../scripts/data-pull.sh). Never edit it by hand: change the pipeline and cut a new release.
 */
import type { DataSource } from "./types";

const json = (load: () => Promise<{ default: unknown }>) => async () => (await load()).default;

export const local: DataSource = {
  name: "local",
  sinturon: {
    records: json(() => import("@/data/sinturon/records.json")),
    cells: json(() => import("@/data/sinturon/cells-3deg.json")),
    latitude: json(() => import("@/data/sinturon/latitude.json")),
    outliers: json(() => import("@/data/sinturon/outliers.json")),
    production: json(() => import("@/data/sinturon/production.json")),
    datasets: json(() => import("@/data/sinturon/datasets.json")),
    summary: json(() => import("@/data/sinturon/summary.json")),
  },
};
