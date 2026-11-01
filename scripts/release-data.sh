#!/usr/bin/env bash
# Packages pipeline/build/v<N> as GitHub Release "data-v<N>" and pins the site to it (data.lock.json).
#   scripts/release-data.sh <N>            package, publish the release, update data.lock.json
#   scripts/release-data.sh <N> --dry-run  package only (dist files in pipeline/build/)
# Releases are immutable: never re-upload a tag; cut the next number instead.
set -euo pipefail
cd "$(dirname "$0")/.."
V="${1:?usage: scripts/release-data.sh <version number> [--dry-run]}"
DIR="pipeline/build/v$V"
[ -f "$DIR/manifest.json" ] || { echo "no $DIR/manifest.json: run pipeline/build.sh $V first" >&2; exit 1; }
ASSET="read-models-v$V.tar.gz"
tar -czf "pipeline/build/$ASSET" -C pipeline/build "v$V"
(cd pipeline/build && shasum -a 256 "$ASSET" > "SHA256SUMS-v$V")
SUM=$(cut -d' ' -f1 "pipeline/build/SHA256SUMS-v$V")
echo "packaged $ASSET ($SUM)"
[ "${2:-}" = "--dry-run" ] && exit 0

NOTES=$(mktemp)
{
  echo "Sinturon data v$V, built $(date +%F)."
  echo
  echo '```'
  python3 -c "import json,sys; m=json.load(open('$DIR/manifest.json')); print('counts:', m['counts']); [print(f\"{k}: {v['bytes']} bytes\") for k,v in m['files'].items()]"
  echo '```'
  echo
  echo "Licences: GBIF records are CC0 1.0 or CC BY 4.0 per record (CC BY-NC excluded); cite GBIF.org and the datasets in sinturon/datasets.json. USDA PSD figures: public domain. Read models: CC BY 4.0. Details: docs/LICENCES.md."
} > "$NOTES"
gh release create "data-v$V" "pipeline/build/$ASSET" "pipeline/build/SHA256SUMS-v$V" "$DIR/manifest.json" \
  --title "Sinturon data v$V ($(date +%F))" --notes-file "$NOTES"
rm -f "$NOTES"
scripts/data-pin.sh "$V" "$SUM"
