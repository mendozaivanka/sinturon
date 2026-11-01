"""Looks up the title, publisher and DOI of every GBIF dataset in the snapshot (CC BY 4.0 asks us to credit each).

    cd pipeline && uv run python gbif/datasets.py      (fetch.py runs this at the end)

Writes gbif/snapshot/datasets.csv: datasetKey, title, publisher, doi, license, records (before dedupe).
"""
import csv, gzip, sys, time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import get_json  # noqa: E402

SNAP = Path(__file__).parent / "snapshot"


def main() -> None:
    with gzip.open(SNAP / "occurrences.csv.gz", "rt") as f:
        counts = Counter(r["datasetKey"] for r in csv.DictReader(f))
    old = {}
    if (SNAP / "datasets.csv").exists():
        with (SNAP / "datasets.csv").open() as f:
            old = {r["datasetKey"]: r for r in csv.DictReader(f)}
    orgs: dict[str, str] = {}
    rows = []
    for i, (key, n) in enumerate(sorted(counts.items(), key=lambda kv: -kv[1])):
        if key in old and old[key]["title"]:
            rows.append(old[key] | {"records": n}); continue
        d = get_json(f"https://api.gbif.org/v1/dataset/{key}")
        org = d.get("publishingOrganizationKey", "")
        if org and org not in orgs:
            orgs[org] = get_json(f"https://api.gbif.org/v1/organization/{org}").get("title", "")
        rows.append({"datasetKey": key, "title": d.get("title", "").strip(), "publisher": orgs.get(org, ""),
                     "doi": d.get("doi", ""), "license": d.get("license", ""), "records": n})
        print(f"  datasets {i + 1}/{len(counts)}", end="\r", flush=True)
        time.sleep(0.1)
    with (SNAP / "datasets.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["datasetKey", "title", "publisher", "doi", "license", "records"], lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote {len(rows)} datasets")


if __name__ == "__main__":
    main()
