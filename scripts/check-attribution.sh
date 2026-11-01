#!/bin/sh
# Fails if any commit in the given range carries an AI attribution line. Used by CI on pull requests and pushes.
#   scripts/check-attribution.sh origin/main..HEAD
range="${1:-HEAD~20..HEAD}"
if git log --format='%H%n%B' "$range" | grep -qiE '^co-authored-by:.*(claude|anthropic|openai|copilot|gpt)|generated with \[?claude|noreply@anthropic\.com'; then
  echo "AI attribution found in commits $range. Reword those commits." >&2
  exit 1
fi
echo "No AI attribution in $range."
