"""Fetches USDA FAS PSD (Production, Supply and Distribution) green coffee and keeps the production rows.

    cd pipeline && uv run python psd/fetch.py          # skips the download when USDA's Last-Modified is unchanged
    cd pipeline && FORCE=1 uv run python psd/fetch.py  # always download

Writes psd/snapshot/production.csv (country × marketing year × Arabica/Robusta/Other/total production, in
1,000 60 kg bags, non-zero country series only) and psd/snapshot/meta.json (Last-Modified, ETag, fetch date).
The zip itself (about 0.4 MB, 9 MB unzipped) goes to psd/raw/, which is git-ignored.
PSD is a US government work: public domain. Cite "USDA Foreign Agricultural Service, PSD Online".
"""
import csv, io, os, sys, urllib.request, zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import CTX, UA, get, write_json  # noqa: E402

URL = "https://apps.fas.usda.gov/psdonline/downloads/psd_coffee_csv.zip"
HERE = Path(__file__).parent
SNAP, RAW = HERE / "snapshot", HERE / "raw"
KEEP = {"Arabica Production": "arabica", "Robusta Production": "robusta", "Other Production": "other", "Production": "total"}


def head() -> dict:
    req = urllib.request.Request(URL, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
        return {"lastModified": r.headers.get("Last-Modified"), "etag": r.headers.get("ETag")}


def main() -> None:
    meta_path = SNAP / "meta.json"
    stamp = head()
    if not os.environ.get("FORCE") and meta_path.exists():
        import json
        old = json.loads(meta_path.read_text())
        if old.get("lastModified") == stamp["lastModified"] and (SNAP / "production.csv").exists():
            print(f"PSD unchanged since {stamp['lastModified']}; keeping the snapshot")
            return
    blob = get(URL, timeout=120)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "psd_coffee_csv.zip").write_bytes(blob)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv"))
        text = z.read(name).decode("utf-8-sig")

    series: dict[tuple, dict] = {}
    released: set[str] = set()
    for r in csv.DictReader(io.StringIO(text)):
        if r["Commodity_Code"] != "0711100" or r["Attribute_Description"] not in KEEP:
            continue
        assert r["Unit_Description"] == "(1000 60 KG BAGS)", r["Unit_Description"]
        k = (r["Country_Code"], r["Country_Name"], int(r["Market_Year"]))
        series.setdefault(k, {})[KEEP[r["Attribute_Description"]]] = float(r["Value"])
        released.add(f"{r['Calendar_Year']}-{r['Month']}")
    nonzero = {(c, n) for (c, n, _), v in series.items() if any(v.values())}
    rows = sorted((k, v) for k, v in series.items() if (k[0], k[1]) in nonzero)

    SNAP.mkdir(parents=True, exist_ok=True)
    with (SNAP / "production.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["psdCode", "country", "marketYear", "arabica", "robusta", "other", "total"])
        for (code, name, year), v in rows:
            w.writerow([code, name, year, *(f"{v.get(x, 0):g}" for x in ("arabica", "robusta", "other", "total"))])
    write_json(meta_path, {
        "url": URL, "fetchedAt": date.today().isoformat(), **stamp, "file": name,
        "unit": "1000 60 kg bags", "latestRelease": max(released),
        "countries": len(nonzero), "rows": len(rows),
    }, indent=1)
    print(f"PSD: {len(rows)} rows, {len(nonzero)} countries with production, release {max(released)}")


if __name__ == "__main__":
    main()
