#!/usr/bin/env bash
# Points the site at data release v<N>: rewrites data.lock.json. The next deploy serves that version.
# Usage: scripts/data-pin.sh <N> <sha256 of read-models-v<N>.tar.gz>
set -euo pipefail
cd "$(dirname "$0")/.."
V="${1:?usage: scripts/data-pin.sh <N> <sha256>}"; SUM="${2:?sha256 required}"
cat > data.lock.json <<JSON
{
  "version": $V,
  "tag": "data-v$V",
  "asset": "read-models-v$V.tar.gz",
  "sha256": "$SUM"
}
JSON
echo "pinned data-v$V"
