/**
 * The shape of every piece of content the site renders, checked at build time. These zod schemas are the data
 * contract: the pipeline (../../../../pipeline/build.py) must produce JSON that passes them, or the build stops with
 * a message naming the bad field. Objects are strict, so an unknown or misspelled field fails too.
 */
import { z } from "astro/zod";

const species = z.enum(["arabica", "robusta", "liberica", "excelsa"]);
const year = z.number().int().nullable();

export const recordsSchema = z.strictObject({
  columns: z.tuple([z.literal("gbifID"), z.literal("species"), z.literal("lat"), z.literal("lon"), z.literal("basis"), z.literal("year"), z.literal("countryCode")]),
  species: z.array(species).length(4),
  basis: z.array(z.string()),
  rows: z.array(z.tuple([z.number().int(), z.number().int().min(0).max(3), z.number().min(-90).max(90), z.number().min(-180).max(180), z.number().int(), year, z.string()])),
});

const cell = z.tuple([z.number(), z.number(), z.number().int().positive(), year, year]);
export const cellsSchema = z.strictObject({
  cellDegrees: z.number(),
  columns: z.array(z.string()),
  species: z.strictObject({ arabica: z.array(cell), robusta: z.array(cell), liberica: z.array(cell), excelsa: z.array(cell) }),
});

const bin = z.union([
  z.strictObject({ from: z.number(), to: z.number(), n: z.number().int() }),
  z.strictObject({ from: z.literal("other"), n: z.number().int() }),
]);
const latStats = z.strictObject({
  n: z.number().int(),
  insideTropics: z.number().int(),
  pctInsideTropics: z.number().nullable(),
  median: z.number().nullable(),
  north: z.number().nullable(),
  south: z.number().nullable(),
  bins10: z.array(bin),
  bins5: z.array(bin),
});
export const latitudeSchema = z.strictObject({
  tropicLat: z.number(),
  species: z.strictObject({ arabica: latStats, robusta: latStats, liberica: latStats, excelsa: latStats, all: latStats }),
});

export const outlierSchema = z.strictObject({
  species,
  lat: z.number(),
  lon: z.number(),
  records: z.number().int().positive(),
  countryCode: z.string(),
  basis: z.array(z.string()),
  firstYear: year,
  lastYear: year,
  institutions: z.array(z.string()),
  locality: z.string(),
  place: z.string(),
  note: z.string(),
  gbifID: z.number().int(),
  why: z.enum(["beyond 35°", "northernmost", "southernmost"]),
});
export const outliersSchema = z.strictObject({ thresholdLat: z.number(), places: z.array(outlierSchema) });

export const productionSchema = z.strictObject({
  unit: z.string(),
  source: z.string(),
  release: z.string().nullable(),
  fetchedAt: z.string().nullable(),
  firstYear: z.number().int(),
  latestYear: z.number().int(),
  forecastYear: z.number().int(),
  note: z.string(),
  columns: z.array(z.string()),
  countries: z.array(z.strictObject({
    code: z.string(),
    name: z.string(),
    series: z.array(z.tuple([z.number().int(), z.number(), z.number(), z.number(), z.number()])),
  })),
});

export const datasetsSchema = z.strictObject({
  datasets: z.array(z.strictObject({
    key: z.string(), title: z.string(), publisher: z.string(), doi: z.string(), licence: z.string(), records: z.number().int(),
  })),
});

const bySpecies = z.strictObject({ arabica: z.number(), robusta: z.number(), liberica: z.number(), excelsa: z.number() });
export const summarySchema = z.strictObject({
  fetchedAt: z.string(),
  species: z.array(species),
  counts: bySpecies,
  countsBeforeDedupe: bySpecies,
  records: z.number().int(),
  dedupe: z.strictObject({
    rule: z.string(),
    before: z.number().int(),
    after: z.number().int(),
    removed: z.number().int(),
    removedBySpecies: z.record(z.string(), z.number()),
    removedByDataset: z.array(z.strictObject({ datasetKey: z.string(), duplicateOf: z.string(), records: z.number().int(), note: z.string() })),
  }),
  gbifQueries: z.array(z.strictObject({ group: z.string(), taxonKey: z.number(), url: z.url(), gbifCount: z.number().int(), rows: z.number().int() })),
  licences: z.record(z.enum(["CC0_1_0", "CC_BY_4_0"]), z.number()),
  basis: z.record(z.string(), z.number()),
  countries: z.number().int(),
  datasets: z.number().int(),
  years: z.strictObject({ first: z.number().int(), last: z.number().int(), undated: z.number().int() }),
  insideTropicsPct: z.strictObject({ arabica: z.number(), robusta: z.number(), liberica: z.number(), excelsa: z.number(), all: z.number() }),
  philippines: z.strictObject({ bySpecies, bySpeciesBeforeDedupe: bySpecies }),
  producingCountries: z.number().int().nullable(),
  psd: z.union([
    z.strictObject({ status: z.literal("ok"), release: z.string().nullable(), latestYear: z.number().int() }),
    z.strictObject({ status: z.literal("missing") }),
  ]),
  citation: z.string(),
  citationNote: z.string(),
});

export type Records = z.infer<typeof recordsSchema>;
export type Cells = z.infer<typeof cellsSchema>;
export type Cell = z.infer<typeof cell>;
export type Latitude = z.infer<typeof latitudeSchema>;
export type LatStats = z.infer<typeof latStats>;
export type Outlier = z.infer<typeof outlierSchema>;
export type Production = z.infer<typeof productionSchema>;
export type Summary = z.infer<typeof summarySchema>;
export type Datasets = z.infer<typeof datasetsSchema>;
