# Sinturon (where the world's coffee has been recorded: the bean belt)

**Live:** https://mendozaivanka.github.io/sinturon/ · **Status (2026-11-02):** v1 built locally, not yet published
· **Data:** [latest.json](https://mendozaivanka.github.io/sinturon/data/latest.json) · [releases](https://github.com/mendozaivanka/sinturon/releases)

Sinturon ("belt" in Filipino) maps 12,514 open GBIF records of the four coffees people drink (arabica, robusta,
liberica and excelsa) and shows that 93% of them lie between the tropics. It names the records far outside the belt
(a greenhouse in Fairbanks, garden plants in Stockholm, a lab sample filed at San Marino's centre point) instead of
hiding them, and sets the records beside USDA's figures for which countries actually grow coffee.

**Records are not farms.** A GBIF record is a herbarium sheet, a phone photo, a garden plant or a lab sample. The map
shows where people collected or saw coffee, which follows where botanists worked. For where coffee is farmed, see the
"Who grows it" page (USDA).

## Layout

| Path | What |
| --- | --- |
| `web/` | The site: Astro 7, React 19 islands, Tailwind v4, shadcn/ui, d3-geo, Nordic Rose (vendored, default palette). Served at `/sinturon/` |
| `pipeline/gbif/` | `fetch.py` pages the GBIF occurrence search API into `snapshot/occurrences.csv.gz`; `datasets.py` adds dataset titles and publishers |
| `pipeline/psd/` | `fetch.py` downloads USDA FAS PSD coffee and keeps the production rows in `snapshot/production.csv` |
| `pipeline/curated/places.psv` | Hand-written names for the outlier places on `/belt/` |
| `pipeline/build.py` | Dedupe, 3° cells, latitude bins, outliers, production, dataset credits, summary |
| `pipeline/build.sh` | Builds one data version into `pipeline/build/v<N>/` with a `manifest.json` (5 MB size guard) |
| `scripts/` | `release-data.sh` (publish `data-v<N>`), `data-pin.sh`, `data-pull.sh` (fetch the pinned release for the site), `check-attribution.sh` |
| `data.lock.json` | The data version the site is pinned to, with its sha256 |
| `docs/` | `DECISIONS.md`, `LICENCES.md`, `PIPELINE.md` |
| `.github/workflows/` | `ci.yml`, `deploy.yml`, `data.yml` (monthly data run) |

## Data sources and licences

| Source | Used for | Licence |
| --- | --- | --- |
| [GBIF](https://www.gbif.org/) occurrence search API | 12,514 records from 355 datasets (fetched 2026-11-01) | CC0 1.0 or CC BY 4.0 per record. CC BY-NC records are never fetched |
| [USDA FAS PSD](https://apps.fas.usda.gov/psdonline/) coffee | Arabica and Robusta production by country, 1960–2026 | Public domain |
| [Natural Earth](https://www.naturalearthdata.com/) 110m land, via `world-atlas` | Map outlines | Public domain |

Cite the records as "GBIF.org (2026-11-01) GBIF Occurrence Search". The search API issues no DOI. Before formal use,
make a GBIF download with the same filters (free account) and cite its DOI instead (`docs/PIPELINE.md`). Every dataset
behind the records is credited in `sinturon/datasets.json` in each release.

### Duplicates

The UPLB Museum of Natural History's herbarium set "Rubiaceae of Luzon Island" is published in GBIF twice (datasets
`2f4e61d3…` and `b96a3e00…`). `build.py` merges records that share species, coordinates (0.01°), year, basis of
record, catalogue number, record number and occurrence ID. v1 removes 45 records this way (12,559 → 12,514), 23 of
them that UPLB copy. All three identifiers are compared together because some gardens give a whole inventory one
batch code as its "catalogue number". Records with none of the three are never merged. Stats are in `summary.json`.

## How the data flows

```
GBIF + USDA ──fetch.py──▶ pipeline/*/snapshot/ (git) ──build.sh──▶ pipeline/build/v<N>/ ──release-data.sh──▶ data-v<N>
                                                                                              │ pinned in data.lock.json
                                                           site build ◀──data-pull.sh─────────┘ (sha256-checked)
```

- **Automatic:** on the 4th of every month `data.yml` refetches GBIF and PSD, rebuilds, checks the site builds on the
  result, and if a read model changed publishes `data-v<N+1>` and opens an "Adopt data" pull request. Merging it
  deploys the new data.
- **Hand-curated:** `pipeline/curated/places.psv` changes only by pull request. CI rebuilds the data from the branch's
  snapshots and reports what changed against the pinned release.

## Run it locally

Node 24, npm and [uv](https://docs.astral.sh/uv/).

```sh
git config core.hooksPath .githooks        # once: blocks AI attribution lines in commit messages
scripts/data-pull.sh                       # fetch the pinned data release
cd web && npm install && npm run dev       # http://localhost:4321/sinturon/
```

Rebuild the data yourself, without releasing: `pipeline/build.sh 1 && scripts/data-pull.sh --local`.
Refetch first with `cd pipeline && uv run python gbif/fetch.py && uv run python psd/fetch.py` (about 5 minutes).

## Cut a data release

Usually the monthly run does it. By hand: Actions → Data → Run workflow. Locally: `pipeline/build.sh <N>`, then
`scripts/release-data.sh <N>` (needs `gh auth login`), commit `data.lock.json`. Roll back by pinning an older version:
`scripts/data-pin.sh <N> <sha256 from that release's SHA256SUMS>`. Releases are never edited or deleted.

## Design system

Nordic Rose, from the private `mendozaivanka/nordic-rose` repo, vendored into `web/`: `npm run design:sync` (needs
`../nordic-rose`) and `npm run design:verify` (hash check, runs in CI). Sinturon uses the default palette; its species
colours and map colours live in `web/src/styles/global.css`.

## Free-tier catches

- GitHub Pages needs a public repo; 1 GB per site, soft 100 GB/month bandwidth, 10 minutes per deploy.
- Scheduled workflows stop after 60 days with no repository activity. Merging the monthly "Adopt data" PR counts;
  GitHub emails before disabling, and Actions → Data → Enable workflow turns it back on.
- GBIF's search API is keyless but caps offset paging at 100,000 records per query (Sinturon needs about 8,000 for its
  largest). Download DOIs need a free GBIF account.
- USDA PSD is a plain download; the fetcher skips it when `Last-Modified` hasn't changed.

## Licence

Code MIT. Read models CC BY 4.0, keeping GBIF's per-dataset credits (`datasets.json`). GBIF records: CC0 1.0 / CC BY
4.0 as marked per dataset. USDA PSD and Natural Earth: public domain. Details in `docs/LICENCES.md`.
