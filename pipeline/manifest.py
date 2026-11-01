"""Writes manifest.json for a built data version: what went in (sources, dates, licences) and what came out (hashes).

Usage: uv run python manifest.py build/v1 v1
"""
import hashlib, json, subprocess, sys
from datetime import date
from pathlib import Path

out, version = Path(sys.argv[1]), sys.argv[2]
here = Path(__file__).parent

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=here).stdout.strip() or "uncommitted"
except OSError:
    commit = "unknown"

gbif = json.loads((here / "gbif/snapshot/meta.json").read_text())
psd_meta = here / "psd/snapshot/meta.json"
psd = json.loads(psd_meta.read_text()) if psd_meta.exists() else None
summary = json.loads((out / "sinturon/summary.json").read_text())

sources = [
    {"id": "gbif", "what": "occurrence records of Coffea arabica, C. canephora (robusta), C. liberica and C. liberica var. dewevrei (excelsa)",
     "url": gbif["api"], "fetchedAt": gbif["fetchedAt"], "retrievedBy": "api", "filters": gbif["filters"],
     "licence": "CC0-1.0 / CC-BY-4.0 per record (CC BY-NC excluded)", "attribution": summary["citation"],
     "datasets": summary["datasets"]},
    {"id": "natural-earth", "what": "land outlines (110m, via the world-atlas npm package) drawn at build time",
     "url": "https://www.naturalearthdata.com/", "licence": "public domain", "attribution": "Made with Natural Earth"},
    {"id": "places", "what": "plain-English names for outlier places", "files": ["curated/places.psv"], "retrievedBy": "hand",
     "licence": "CC-BY-4.0", "attribution": "Sinturon"},
]
if psd:
    sources.append({"id": "usda-psd", "what": "green coffee production by country and marketing year (Arabica, Robusta, Other)",
                    "url": psd["url"], "fetchedAt": psd["fetchedAt"], "lastModified": psd.get("lastModified"), "retrievedBy": "download",
                    "licence": "public domain (US government work)", "attribution": "USDA Foreign Agricultural Service, PSD Online"})

manifest = {
    "version": version,
    "builtAt": date.today().isoformat(),
    "pipelineCommit": commit,
    "sources": sources,
    "files": {str(p.relative_to(out)): {"bytes": p.stat().st_size, "sha256": sha(p)}
              for p in sorted(out.rglob("*.json")) if p.name != "manifest.json"},
    "counts": {"records": summary["records"], **summary["counts"], "removedAsDuplicates": summary["dedupe"]["removed"],
               "producingCountries": summary.get("producingCountries")},
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
total = sum(f["bytes"] for f in manifest["files"].values())
print(f"manifest: {len(manifest['files'])} files, {total / 1024:.0f} KB, counts {manifest['counts']}")
if total > 5 * 1024 * 1024:
    sys.exit(f"size guard: read models are {total / 1048576:.1f} MB (limit 5 MB). Record why in docs/DECISIONS.md and raise it.")
