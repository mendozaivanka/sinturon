"""Turns the GBIF and PSD snapshots into the read models the site reads.

    cd pipeline && uv run python build.py build/v1/sinturon

Inputs (committed snapshots):  gbif/snapshot/occurrences.csv.gz, gbif/snapshot/datasets.csv, gbif/snapshot/meta.json,
                               psd/snapshot/production.csv, psd/snapshot/meta.json (optional), curated/places.psv
Outputs (in the given folder): records.json, cells-3deg.json, latitude.json, outliers.json, production.json,
                               summary.json
"""
import csv, gzip, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

from common import write_json

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "build/dev/sinturon"
SPECIES = ["arabica", "robusta", "liberica", "excelsa"]
TROPIC = 23.44
CELL = 3
OUTLIER_LAT = 35

# The UPLB Museum of Natural History's "Rubiaceae of Luzon Island" herbarium set is published in GBIF twice.
KNOWN_DUPLICATE_DATASETS = {
    "2f4e61d3-886a-43ce-b7ae-55644fdfdb2e": "Rubiaceae of Luzon Island (UPLB), copy A",
    "b96a3e00-ec8b-4885-a509-d4234aaab7bb": "Rubiaceae of Luzon Island (UPLB), copy B",
}


def num(x: str):
    return int(x) if x not in ("", None) else None


def load_records() -> list[dict]:
    with gzip.open(HERE / "gbif/snapshot/occurrences.csv.gz", "rt") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["gbifID"] = int(r["gbifID"]); r["lat"] = float(r["lat"]); r["lon"] = float(r["lon"]); r["year"] = num(r["year"])
    rows.sort(key=lambda r: r["gbifID"])
    return rows


def dedupe(rows: list[dict]) -> tuple[list[dict], dict]:
    """The same specimen published twice: same species, place (0.01°), year, basis of record, and the same
    catalogue number, record number and occurrence ID (all three compared together, so a batch code shared by a
    garden's whole inventory does not merge distinct plants). Records with none of the three are never merged:
    two observations at one spot in one year can be genuinely different plants."""
    kept, seen, removed = [], {}, []
    for r in rows:
        ident = tuple(r[c].strip().lower() for c in ("catalogNumber", "recordNumber", "occurrenceID"))
        if not any(ident):
            kept.append(r); continue
        k = (r["species"], r["lat"], r["lon"], r["year"], r["basisOfRecord"], *ident)
        if k in seen:
            removed.append((r, seen[k]))
        else:
            seen[k] = r; kept.append(r)
    pairs = Counter((d["datasetKey"], o["datasetKey"]) for d, o in removed)
    stats = {
        "rule": "same species, coordinates (0.01°), year, basis of record, catalogue number, record number and occurrence ID",
        "before": len(rows),
        "after": len(kept),
        "removed": len(removed),
        "removedBySpecies": dict(Counter(d["species"] for d, _ in removed)),
        "removedByDataset": [
            {"datasetKey": a, "duplicateOf": b, "records": n,
             "note": KNOWN_DUPLICATE_DATASETS.get(a, "") if a in KNOWN_DUPLICATE_DATASETS and b in KNOWN_DUPLICATE_DATASETS else ""}
            for (a, b), n in pairs.most_common()
        ],
    }
    return kept, stats


def cells(rows):
    out = {}
    for sp in SPECIES:
        acc = defaultdict(lambda: [0, None, None])
        for r in rows:
            if r["species"] != sp:
                continue
            la = math.floor(r["lat"] / CELL) * CELL + CELL / 2
            lo = math.floor(r["lon"] / CELL) * CELL + CELL / 2
            c = acc[(la, lo)]
            c[0] += 1
            if r["year"]:
                c[1] = r["year"] if c[1] is None else min(c[1], r["year"])
                c[2] = r["year"] if c[2] is None else max(c[2], r["year"])
        out[sp] = sorted([[la, lo, n, a, b] for (la, lo), (n, a, b) in acc.items()], key=lambda c: -c[2])
    return {"cellDegrees": CELL, "columns": ["lat", "lon", "n", "firstYear", "lastYear"], "species": out}


def latitude(rows):
    def bins(sp_rows, size):
        c = Counter(math.floor(r["lat"] / size) * size for r in sp_rows)
        lo, hi = -60, 70
        return [{"from": b, "to": b + size, "n": c.get(b, 0)} for b in range(lo, hi, size)] + (
            [{"from": "other", "n": sum(v for k, v in c.items() if k < lo or k >= hi)}] if any(k < lo or k >= hi for k in c) else [])

    out = {"tropicLat": TROPIC, "species": {}}
    for sp in SPECIES + ["all"]:
        s = rows if sp == "all" else [r for r in rows if r["species"] == sp]
        inside = sum(1 for r in s if abs(r["lat"]) <= TROPIC)
        lats = sorted(r["lat"] for r in s)
        out["species"][sp] = {
            "n": len(s),
            "insideTropics": inside,
            "pctInsideTropics": round(100 * inside / len(s), 1) if s else None,
            "median": lats[len(lats) // 2] if lats else None,
            "north": lats[-1] if lats else None,
            "south": lats[0] if lats else None,
            "bins10": bins(s, 10),
            "bins5": bins(s, 5),
        }
    return out


def load_places():
    p = HERE / "curated/places.psv"
    if not p.exists():
        return []
    with p.open() as f:
        return [r for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="|")]


def outliers(rows):
    """Places with records beyond 35° from the equator, plus each species' northernmost and southernmost place.
    One row per species and place (0.1°), so a garden with forty sheets is one row."""
    places = load_places()
    groups = defaultdict(list)
    for r in rows:
        groups[(r["species"], round(r["lat"], 1), round(r["lon"], 1))].append(r)
    extremes = set()
    for sp in SPECIES:
        keys = [k for k in groups if k[0] == sp]
        if keys:
            extremes.add(max(keys, key=lambda k: k[1])); extremes.add(min(keys, key=lambda k: k[1]))
    out = []
    for k, rs in groups.items():
        sp, la, lo = k
        if abs(la) <= OUTLIER_LAT and k not in extremes:
            continue
        years = [r["year"] for r in rs if r["year"]]
        label = next((p for p in places if p["species"] == sp and abs(float(p["lat"]) - la) <= 0.2 and abs(float(p["lon"]) - lo) <= 0.2), None)
        loc = Counter(r["locality"] for r in rs if r["locality"]).most_common(1)
        out.append({
            "species": sp, "lat": la, "lon": lo, "records": len(rs),
            "countryCode": Counter(r["countryCode"] for r in rs).most_common(1)[0][0],
            "basis": sorted({r["basisOfRecord"] for r in rs}),
            "firstYear": min(years) if years else None, "lastYear": max(years) if years else None,
            "institutions": sorted({r["institutionCode"] for r in rs if r["institutionCode"]})[:4],
            "locality": loc[0][0] if loc else "",
            "place": label["place"] if label else "",
            "note": label["note"] if label else "",
            "gbifID": rs[0]["gbifID"],
            "why": "beyond 35°" if abs(la) > OUTLIER_LAT else ("northernmost" if k == max((g for g in groups if g[0] == sp), key=lambda g: g[1]) else "southernmost"),
        })
    out.sort(key=lambda o: -abs(o["lat"]))
    return {"thresholdLat": OUTLIER_LAT, "places": out}


def production():
    p = HERE / "psd/snapshot/production.csv"
    if not p.exists():
        return None
    meta_p = HERE / "psd/snapshot/meta.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    by = defaultdict(list)
    names = {}
    with p.open() as f:
        for r in csv.DictReader(f):
            names[r["psdCode"]] = r["country"]
            by[r["psdCode"]].append([int(r["marketYear"]), *(float(r[k]) for k in ("arabica", "robusta", "other", "total"))])
    years = sorted({y for s in by.values() for y, *_ in s})
    latest = years[-1]
    countries = [{"code": c, "name": names[c], "series": sorted(s)} for c, s in by.items()]
    countries.sort(key=lambda c: -next((t for y, a, r, o, t in c["series"] if y == latest - 1), 0))
    return {
        "unit": "1,000 60 kg bags (green coffee)",
        "source": "USDA Foreign Agricultural Service, PSD Online",
        "release": meta.get("latestRelease"), "fetchedAt": meta.get("fetchedAt"),
        "firstYear": years[0], "latestYear": latest, "forecastYear": latest,
        "note": "Marketing years. The latest year is a USDA forecast; earlier recent years are estimates and get revised.",
        "columns": ["marketYear", "arabica", "robusta", "other", "total"],
        "countries": countries,
    }


def datasets(rows):
    """Every GBIF dataset behind the kept records, with its publisher and licence: CC BY 4.0 asks for credit."""
    p = HERE / "gbif/snapshot/datasets.csv"
    info = {}
    if p.exists():
        with p.open() as f:
            info = {r["datasetKey"]: r for r in csv.DictReader(f)}
    n = Counter(r["datasetKey"] for r in rows)
    lic = defaultdict(Counter)
    for r in rows:
        lic[r["datasetKey"]][r["license"]] += 1
    out = [{"key": k, "title": info.get(k, {}).get("title", ""), "publisher": info.get(k, {}).get("publisher", ""),
            "doi": info.get(k, {}).get("doi", ""), "licence": lic[k].most_common(1)[0][0], "records": c}
           for k, c in n.most_common()]
    return {"datasets": out}


def main() -> None:
    gmeta = json.loads((HERE / "gbif/snapshot/meta.json").read_text())
    raw = load_records()
    rows, dd = dedupe(raw)
    basis = sorted({r["basisOfRecord"] for r in rows})
    countries = sorted({r["countryCode"] for r in rows if r["countryCode"]})
    write_json(OUT / "records.json", {
        "columns": ["gbifID", "species", "lat", "lon", "basis", "year", "countryCode"],
        "species": SPECIES, "basis": basis,
        "rows": [[r["gbifID"], SPECIES.index(r["species"]), r["lat"], r["lon"], basis.index(r["basisOfRecord"]), r["year"], r["countryCode"]] for r in rows],
    })
    write_json(OUT / "cells-3deg.json", cells(rows))
    lat = latitude(rows)
    write_json(OUT / "latitude.json", lat)
    write_json(OUT / "outliers.json", outliers(rows))
    prod = production()
    if prod:
        write_json(OUT / "production.json", prod)
    write_json(OUT / "datasets.json", datasets(rows))

    ph =[r for r in rows if r["countryCode"] == "PH"]
    ph_raw = [r for r in raw if r["countryCode"] == "PH"]
    summary = {
        "fetchedAt": gmeta["fetchedAt"],
        "species": SPECIES,
        "counts": {sp: sum(1 for r in rows if r["species"] == sp) for sp in SPECIES},
        "countsBeforeDedupe": {sp: sum(1 for r in raw if r["species"] == sp) for sp in SPECIES},
        "records": len(rows),
        "dedupe": dd,
        "gbifQueries": gmeta["queries"],
        "licences": dict(Counter(r["license"] for r in rows)),
        "basis": dict(Counter(r["basisOfRecord"] for r in rows).most_common()),
        "countries": len(countries),
        "datasets": len({r["datasetKey"] for r in rows}),
        "years": {"first": min(r["year"] for r in rows if r["year"]), "last": max(r["year"] for r in rows if r["year"]),
                  "undated": sum(1 for r in rows if not r["year"])},
        "insideTropicsPct": {sp: lat["species"][sp]["pctInsideTropics"] for sp in SPECIES + ["all"]},
        "philippines": {
            "bySpecies": {sp: sum(1 for r in ph if r["species"] == sp) for sp in SPECIES},
            "bySpeciesBeforeDedupe": {sp: sum(1 for r in ph_raw if r["species"] == sp) for sp in SPECIES},
        },
        "producingCountries": len(prod["countries"]) if prod else None,
        "psd": {"status": "ok", "release": prod["release"], "latestYear": prod["latestYear"]} if prod else {"status": "missing"},
        "citation": f"GBIF.org ({gmeta['fetchedAt']}) GBIF Occurrence Search https://www.gbif.org/occurrence/search",
        "citationNote": "Fetched with the GBIF occurrence search API, which issues no DOI. For formal citation, replace this "
                        "with a GBIF download DOI made with the same filters (docs/PIPELINE.md).",
    }
    write_json(OUT / "summary.json", summary, indent=1)
    print(f"records {len(raw)} → {len(rows)} after dedupe (−{dd['removed']}); {summary['counts']}; tropics {summary['insideTropicsPct']}")


if __name__ == "__main__":
    main()
