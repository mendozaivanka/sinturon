# Decisions

Append-only. Newest last.

- **2026-11-01 · Own repo, Timpla's conventions.** Sinturon is a sibling of Timpla in `mendozaivanka/sinturon`: same
  release flow (`data-v<N>` pinned by `data.lock.json`, sha256-checked at deploy), same workflows, hooks and vendored
  Nordic Rose. It uses the **default** Nordic Rose palette, not a coffee palette.
- **2026-11-01 · GBIF search API for v1, download DOI later.** The keyless occurrence search API (300 per page) is
  enough for about 12,600 records and needs no account. It issues no DOI, so the citation is "GBIF.org (date) GBIF
  Occurrence Search" with a note; a GBIF download with the same filters replaces it before any formal use.
- **2026-11-01 · Licence filter at the source.** Only `license=CC0_1_0` and `license=CC_BY_4_0` are requested; CC BY-NC
  records are never fetched. Filters also require coordinates and no flagged geospatial issue.
- **2026-11-01 · Excelsa split out of liberica.** Records whose taxon key or accepted taxon key is 2895394
  (C. liberica var. dewevrei) or 2895399 (its synonym C. dewevrei), or whose name contains "dewevrei", are excelsa.
- **2026-11-01 · Deduplication rule.** Merge only when species, 0.01° coordinates, year, basis of record, catalogue
  number, record number and occurrence ID all match. A looser rule (catalogue number alone) merged 434 records,
  including about 180 distinct plants in a Guinean garden inventory that shares one batch code; the strict rule
  removes 45, including the 23 duplicates of UPLB's "Rubiaceae of Luzon Island" set, which is published twice.
- **2026-11-01 · Snapshots in git.** `occurrences.csv.gz` (gzipped with a fixed timestamp, about 370 KB) and the PSD
  production extract (about 110 KB) are committed so `build.sh` works offline and every version is reproducible. The
  raw PSD zip is not committed.
- **2026-11-01 · 3° cells and sized circles, not hexes.** Records are counted in 3° cells and drawn as translucent
  circles (area ∝ count, shared scale) on an Equal Earth map rendered to SVG at build time. No tiles, no MapLibre:
  the whole map is a few hundred circles. H3 hexes can come later if the map needs zooming.
- **2026-11-01 · Outliers named, not clipped.** Every place beyond 35° and each species' northern and southern
  extreme is listed on `/belt/`; `curated/places.psv` gives the ones checked by hand a plain name.
- **2026-11-01 · Change detection ignores summary.json.** It carries the fetch date and would make every monthly run
  a "change"; a real change shows up in `records.json` or `production.json`.
