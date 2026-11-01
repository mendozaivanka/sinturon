#!/usr/bin/env bash
# Downloads the data release pinned in data.lock.json, checks its sha256, and unpacks it for the web build:
#   web/src/data/sinturon/                       read by the site's data layer at build time
#   web/public/data/v<N>/, web/public/data/latest.json   published at /sinturon/data/ for anyone to reuse
# Usage: scripts/data-pull.sh            (from the release; the repo is public, so no token is needed)
#        scripts/data-pull.sh --local    (from pipeline/build/v<N>, for testing a build before releasing it)
set -euo pipefail
cd "$(dirname "$0")/.."
V=$(python3 -c "import json; print(json.load(open('data.lock.json'))['version'])")
ASSET=$(python3 -c "import json; print(json.load(open('data.lock.json'))['asset'])")
SUM=$(python3 -c "import json; print(json.load(open('data.lock.json'))['sha256'])")
REPO="${GITHUB_REPOSITORY:-mendozaivanka/sinturon}"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

if [ "${1:-}" = "--local" ]; then
  [ -d "pipeline/build/v$V" ] || { echo "no pipeline/build/v$V: run pipeline/build.sh $V" >&2; exit 1; }
  cp -R "pipeline/build/v$V" "$TMP/v$V"
  echo "using local pipeline/build/v$V (not verified against the release)"
else
  curl -fsSL "https://github.com/$REPO/releases/download/data-v$V/$ASSET" -o "$TMP/$ASSET"
  echo "$SUM  $TMP/$ASSET" | shasum -a 256 -c - >/dev/null || { echo "sha256 mismatch for $ASSET" >&2; exit 1; }
  tar -xzf "$TMP/$ASSET" -C "$TMP"
  echo "downloaded data-v$V ($ASSET), sha256 ok"
fi

rm -rf web/src/data/sinturon web/public/data
mkdir -p web/src/data web/public/data
cp -R "$TMP/v$V/sinturon" web/src/data/sinturon
cp -R "$TMP/v$V" "web/public/data/v$V"
BUILT=$(python3 -c "import json; print(json.load(open('$TMP/v$V/manifest.json'))['builtAt'])")
cat > web/public/data/latest.json <<JSON
{ "current": "v$V", "base": "v$V/", "builtAt": "$BUILT", "release": "https://github.com/$REPO/releases/tag/data-v$V" }
JSON
echo "unpacked v$V into web/src/data and web/public/data"
