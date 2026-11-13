"""Downloads JAKIM's official prayer times (e-solat.gov.my) for every zone used in places-my.json.

    python3 .github/ezan-pages/fetch_jakim.py [YEAR ...]     # default: this year and next year

Writes data/jakim-<year>.json: {zone: {"YYYY-MM-DD": [hijri, imsak, subuh, syuruk, zohor, asar, maghrib, isyak]}}.
A year that is already complete on disk is not downloaded again, so the nightly workflow only calls
JAKIM when a new year appears; if JAKIM is unreachable the pages are built from what is on disk.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://www.e-solat.gov.my/index.php?r=esolatApi/takwimsolat&period=duration&zone={zone}"
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mac Apr Mei Jun Jul Ogos Sep Okt Nov Dis".split())}
KEYS = ("imsak", "fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha")


def fetch(zone, year):
    body = urllib.parse.urlencode({"datestart": f"{year}-01-01", "dateend": f"{year}-12-31"}).encode()
    req = urllib.request.Request(API.format(zone=zone), data=body,
                                 headers={"User-Agent": "Mozilla/5.0 (Ezan Vakti pages; labsmugi.github.io)"})
    rows = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())["prayerTime"]
    if not isinstance(rows, list):  # {"data": ["No data available ..."]}: not published yet (Selangor, Sabah)
        raise RuntimeError("not published yet")
    out = {}
    for r in rows:
        d, m, y = r["date"].split("-")
        iso = date(int(y), MONTHS[m], int(d)).isoformat()
        out[iso] = [r["hijri"]] + [r[k][:5] for k in KEYS]
    return out


def main():
    years = [int(y) for y in sys.argv[1:]] or [date.today().year, date.today().year + 1]
    places = json.load(open(os.path.join(HERE, "places-my.json"), encoding="utf-8"))
    zones = sorted({p["zone"] for g in places for p in g["places"]})
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    for year in years:
        path = os.path.join(HERE, "data", f"jakim-{year}.json")
        data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        days = 366 if year % 4 == 0 and (year % 100 or year % 400 == 0) else 365
        changed = False
        for z in zones:
            if len(data.get(z, {})) >= days:
                continue
            try:
                data[z] = fetch(z, year)
                changed = True
                print(f"{year} {z}: {len(data[z])} days")
            except Exception as e:  # keep what we have; the next run tries again
                print(f"{year} {z}: failed ({e})", file=sys.stderr)
            time.sleep(1)
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"), sort_keys=True)
                f.write("\n")


if __name__ == "__main__":
    main()
