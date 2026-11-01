"""Fetches every open-licence, cleanly georeferenced GBIF occurrence of the four coffees into a snapshot.

    cd pipeline && uv run python gbif/fetch.py

Writes gbif/snapshot/occurrences.csv.gz (one row per GBIF record, before deduplication; gzipped with a fixed
timestamp so an unchanged fetch gives identical bytes) and gbif/snapshot/meta.json
(fetch date, the exact queries, GBIF's reported count per query). The build step (build.py) dedupes and bins.

Queries the occurrence *search* API (300 per page, offset paging, keyless). Filters, all applied by GBIF:
hasCoordinate=true, hasGeospatialIssue=false, license in (CC0_1_0, CC_BY_4_0). CC BY-NC records are never fetched.
For a formal citation, a GBIF *download* (free account) with the same filters gives a DOI; see docs/PIPELINE.md.
"""
import csv, gzip, io, sys, time, urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import get_json, write_json  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

API = "https://api.gbif.org/v1/occurrence/search"
PAGE = 300
OUT = Path(__file__).parent / "snapshot"

# GBIF backbone keys. C. liberica (8524134) includes var. dewevrei ("excelsa"), split out below.
QUERIES = {
    "arabica": 2895345,   # Coffea arabica L.
    "robusta": 2895528,   # Coffea canephora Pierre ex A.Froehner
    "liberica": 8524134,  # Coffea liberica W.Bull (incl. var. dewevrei)
}
EXCELSA_KEYS = {2895394, 2895399}  # C. liberica var. dewevrei; its synonym C. dewevrei De Wild. & T.Durand
LICENCES = {
    "http://creativecommons.org/publicdomain/zero/1.0/legalcode": "CC0_1_0",
    "http://creativecommons.org/licenses/by/4.0/legalcode": "CC_BY_4_0",
}
FILTERS = [("hasCoordinate", "true"), ("hasGeospatialIssue", "false"), ("license", "CC0_1_0"), ("license", "CC_BY_4_0")]
COLUMNS = ["gbifID", "species", "lat", "lon", "basisOfRecord", "year", "countryCode", "datasetKey", "institutionCode",
           "license", "catalogNumber", "recordNumber", "occurrenceID", "taxonKey", "acceptedTaxonKey", "scientificName",
           "locality", "stateProvince"]


def classify(group: str, r: dict) -> str:
    if group != "liberica":
        return group
    keys = {r.get("taxonKey"), r.get("acceptedTaxonKey")}
    if keys & EXCELSA_KEYS or "dewevrei" in (r.get("scientificName") or "").lower():
        return "excelsa"
    return "liberica"


def row(species: str, r: dict) -> dict | None:
    lic = LICENCES.get(r.get("license", ""))
    if lic is None:  # belt and braces: the query already filters licences
        return None
    lat, lon = r.get("decimalLatitude"), r.get("decimalLongitude")
    if lat is None or lon is None:
        return None
    return {
        "gbifID": r["key"],
        "species": species,
        "lat": round(lat, 2),
        "lon": round(lon, 2),
        "basisOfRecord": r.get("basisOfRecord", ""),
        "year": r.get("year", ""),
        "countryCode": r.get("countryCode", ""),
        "datasetKey": r.get("datasetKey", ""),
        "institutionCode": r.get("institutionCode", ""),
        "license": lic,
        "catalogNumber": r.get("catalogNumber", ""),
        "recordNumber": r.get("recordNumber", ""),
        "occurrenceID": r.get("occurrenceID", ""),
        "taxonKey": r.get("taxonKey", ""),
        "acceptedTaxonKey": r.get("acceptedTaxonKey", ""),
        "scientificName": r.get("scientificName", ""),
        "locality": (r.get("locality") or r.get("verbatimLocality") or "").replace("\n", " ").strip()[:120],
        "stateProvince": r.get("stateProvince", ""),
    }


def fetch(group: str, key: int) -> tuple[list[dict], int, str]:
    params = [("taxonKey", str(key)), *FILTERS]
    url = f"{API}?{urllib.parse.urlencode(params)}"
    rows, offset, count = [], 0, None
    while True:
        page = get_json(f"{url}&limit={PAGE}&offset={offset}")
        count = page["count"] if count is None else count
        for r in page["results"]:
            x = row(group, r)
            if x:
                x["species"] = classify(group, r)
                rows.append(x)
        offset += PAGE
        print(f"  {group}: {min(offset, count)}/{count}", end="\r", flush=True)
        if page.get("endOfRecords") or offset >= count:
            break
        time.sleep(0.25)
    print()
    return rows, count, url


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows, queries = [], []
    for group, key in QUERIES.items():
        rows, count, url = fetch(group, key)
        all_rows += rows
        queries.append({"group": group, "taxonKey": key, "url": url, "gbifCount": count, "rows": len(rows)})
    # A record can only come back once per query, but guard against the API returning one twice across pages.
    seen, unique = set(), []
    for r in all_rows:
        if r["gbifID"] not in seen:
            seen.add(r["gbifID"]); unique.append(r)
    unique.sort(key=lambda r: (r["species"], r["gbifID"]))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader(); w.writerows(unique)
    (OUT / "occurrences.csv.gz").write_bytes(gzip.compress(buf.getvalue().encode(), compresslevel=9, mtime=0))
    by_species: dict[str, int] = {}
    for r in unique:
        by_species[r["species"]] = by_species.get(r["species"], 0) + 1
    write_json(OUT / "meta.json", {
        "fetchedAt": date.today().isoformat(),
        "fetchedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "api": API,
        "filters": dict(FILTERS[:2]) | {"license": ["CC0_1_0", "CC_BY_4_0"]},
        "excelsaTaxonKeys": sorted(EXCELSA_KEYS),
        "queries": queries,
        "rowsBySpecies": by_species,
        "rows": len(unique),
    }, indent=1)
    print(f"wrote {len(unique)} records: {by_species}")
    import datasets
    datasets.main()


if __name__ == "__main__":
    main()
