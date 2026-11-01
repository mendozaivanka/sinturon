# Licences and attribution

| Source | Used for | Licence | Attribution shown | Republished raw? |
| --- | --- | --- | --- | --- |
| GBIF occurrence search API (accessed 2026-11-01) | where the four coffees have been recorded | CC0 1.0 or CC BY 4.0, per record and dataset; CC BY-NC records excluded at the query | "GBIF.org (date) GBIF Occurrence Search"; every dataset title, publisher and DOI in `datasets.json` and the top 25 on `/data/` | Yes, a column subset in `pipeline/gbif/snapshot/occurrences.csv.gz` |
| USDA FAS PSD Online, coffee (accessed 2026-11-01, release 2026-07) | production by country and marketing year | public domain (US government work) | "USDA Foreign Agricultural Service, PSD Online" | Production rows only, `pipeline/psd/snapshot/production.csv` |
| Natural Earth 110m land (world-atlas 2.0.2) | map outlines | public domain | "Natural Earth" in the footer | Bundled by npm, not committed |
| `pipeline/curated/places.psv` | outlier place names | CC BY 4.0 (Sinturon) | n/a | Yes |

Planned, not yet used: WCVP (Kew, CC BY 4.0) for native ranges; Timpla's PSA-based release for the Barako chapter
(attribute the Philippine Statistics Authority).

Read models in each release are CC BY 4.0. Anyone reusing them must keep the GBIF credits.
Not used: CC BY-NC GBIF records, Google or Foursquare data, WorldClim (non-commercial), modelled suitability layers.
