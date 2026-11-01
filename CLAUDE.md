# sinturon

Sinturon's site (`web/`, Astro 7 + React + d3-geo + Nordic Rose) and its data pipeline (`pipeline/`). Deployed to
GitHub Pages at https://mendozaivanka.github.io/sinturon/ by `.github/workflows/deploy.yml`. README.md has the details.
Sibling of `../timpla`, whose conventions it copies.

- **Data reaches the site only through releases.** `pipeline/build.sh <N>` → `scripts/release-data.sh <N>` publishes
  `data-v<N>` and pins it in `data.lock.json`; `scripts/data-pull.sh` unpacks the pinned release into
  `web/src/data/sinturon/` (git-ignored). Never hand-edit those JSON files or a published release.
- **Fetch and build are separate.** `pipeline/gbif/fetch.py` and `pipeline/psd/fetch.py` write committed snapshots;
  `build.sh` reads only the snapshots, so any build is reproducible from git.
- **Open licences only:** GBIF records with CC0_1_0 or CC_BY_4_0 (never CC BY-NC), USDA PSD (public domain), Natural
  Earth (public domain). Free services only.
- **Wording:** "recorded", never "grown", for GBIF; "USDA estimates" for PSD, and the latest marketing year is a
  forecast. Outliers are named and kept, never clipped. No modelled or estimated layers.
- **Curated input** (`pipeline/curated/places.psv`) is edited by hand; each note describes what the GBIF record says.
- **Base path:** the site lives under `/sinturon`. Internal links are written `/sinturon/...`; files in `web/public/`
  must use `import.meta.env.BASE_URL`.
- **Design system:** files from `../nordic-rose` are vendored (`npm run design:sync`), never edited here. Default
  palette (no `data-palette`); species and map colours are in `web/src/styles/global.css`.
- Python via `uv` in `pipeline/`; macOS Python has no CA bundle, so HTTPS goes through `certifi` (`pipeline/common.py`).
- Astro's compiler misreads `x! / y` as a regex in `.astro` files: write `(x ?? 0) / y`.
- **Commits and PRs carry no AI attribution** (no Co-Authored-By Claude, no "Generated with Claude Code").
- Verify with `pipeline/build.sh 1 && scripts/data-pull.sh --local` and `cd web && npm run build`. Commit/push only when asked.
