# Pipeline runbook

## Stages

1. `pipeline/gbif/fetch.py`: GBIF occurrence search, three taxon queries (arabica 2895345, canephora 2895528,
   liberica 8524134 incl. var. dewevrei), 300 per page, filters `hasCoordinate=true`, `hasGeospatialIssue=false`,
   `license=CC0_1_0`, `license=CC_BY_4_0` → `gbif/snapshot/occurrences.csv.gz` + `meta.json`. Then `gbif/datasets.py`
   → `datasets.csv` (titles, publishers, DOIs; cached rows are reused). About 5 minutes.
2. `pipeline/psd/fetch.py`: USDA PSD coffee zip → `psd/snapshot/production.csv` + `meta.json`. Skips when
   `Last-Modified` is unchanged (`FORCE=1` to override). If USDA is down, the last snapshot stays and the build uses it.
3. `pipeline/build.py` (via `build.sh <N>`): dedupe → `records.json`, `cells-3deg.json`, `latitude.json`,
   `outliers.json`, `production.json`, `datasets.json`, `summary.json` in `build/v<N>/sinturon/`.
4. `pipeline/manifest.py`: sources, licences, file hashes, counts; fails over 5 MB.
5. `scripts/release-data.sh <N>`: tarball + SHA256SUMS + manifest as release `data-v<N>`; pins `data.lock.json`.

## Situations

| Situation | What happens | What to do |
| --- | --- | --- |
| GBIF fetch fails in the monthly run | the run fails before building; an issue opens | rerun later (Actions → Data) |
| GBIF counts jump or drop | the run summary shows counts old → new | read `summary.json` (`gbifQueries`, `dedupe`) before merging the PR |
| A new duplicated dataset appears | `summary.json → dedupe.removedByDataset` lists it | add a note in `KNOWN_DUPLICATE_DATASETS` in `build.py` |
| PSD layout changes | `psd/fetch.py` stops on the unit assertion | update the parser, PR |
| Nothing changed | no release, no PR | nothing |
| Site fails to build on new data | no release | fix the schema (`web/src/lib/data/schemas.ts`) or the pipeline in a PR |
| Bad data went live | | pin the previous version: `scripts/data-pin.sh <N-1> <sha256>`, PR, merge |
| Workflow disabled after 60 quiet days | the monthly run stops | Actions → Data → Enable workflow |

## A citable GBIF download (do before formal use)

The search API gives no DOI. With a free GBIF account, request one download per taxon key with the same filters
(`TAXON_KEY`, `HAS_COORDINATE=true`, `HAS_GEOSPATIAL_ISSUE=false`, `LICENSE in (CC0_1_0, CC_BY_4_0)`) at
https://www.gbif.org/occurrence/search or via `POST https://api.gbif.org/v1/occurrence/download/request`, then record
the DOIs in `summary.json`'s citation (a small change to `build.py`) and on `/data/`. Credentials go in repository
secrets, never in git.
