"""Builds places-id.json (Indonesia) and places-my.json (Malaysia) from GeoNames and JAKIM's zone list.

Run once by hand, not in the workflow:
    curl -O https://download.geonames.org/export/dump/cities15000.zip && unzip cities15000.zip
    curl -O https://download.geonames.org/export/dump/MY.zip && unzip MY.zip
    curl -o esolat.html https://www.e-solat.gov.my/index.php?siteId=24&pageId=24
    python3 prepare_intl.py cities15000.txt MY.txt esolat.html

Indonesia: every GeoNames town of 50,000+ people, grouped by province (Indonesian names).
Malaysia: the towns JAKIM lists for each prayer-time zone; coordinates (for the qibla only, the times
come from JAKIM) from GeoNames, or the zone's other towns when GeoNames doesn't know the town.
Data: GeoNames (CC BY 4.0), JAKIM e-Solat.
"""
import csv
import html
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

ID_PROVINCES = {
    "01": "Aceh", "02": "Bali", "03": "Bengkulu", "04": "DKI Jakarta", "05": "Jambi", "07": "Jawa Tengah",
    "08": "Jawa Timur", "10": "DI Yogyakarta", "11": "Kalimantan Barat", "12": "Kalimantan Selatan",
    "13": "Kalimantan Tengah", "14": "Kalimantan Timur", "15": "Lampung", "17": "Nusa Tenggara Barat",
    "18": "Nusa Tenggara Timur", "21": "Sulawesi Tengah", "22": "Sulawesi Tenggara", "24": "Sumatera Barat",
    "26": "Sumatera Utara", "28": "Maluku", "29": "Maluku Utara", "30": "Jawa Barat", "31": "Sulawesi Utara",
    "32": "Sumatera Selatan", "33": "Banten", "34": "Gorontalo", "35": "Kepulauan Bangka Belitung",
    "36": "Papua", "37": "Riau", "38": "Sulawesi Selatan", "39": "Papua Barat", "40": "Kepulauan Riau",
    "41": "Sulawesi Barat", "42": "Kalimantan Utara", "PD": "Papua Barat Daya", "PT": "Papua Tengah",
    "PE": "Papua Pegunungan", "PS": "Papua Selatan",
}
ID_FIX = {"Jambi City": "Jambi", "South Tangerang": "Tangerang Selatan", "Ciranjang-hilir": "Ciranjang"}

MY_STATES = {"JHR": "Johor", "KDH": "Kedah", "KTN": "Kelantan", "MLK": "Melaka", "NGS": "Negeri Sembilan",
             "PHG": "Pahang", "PLS": "Perlis", "PNG": "Pulau Pinang", "PRK": "Perak", "SBH": "Sabah",
             "SGR": "Selangor", "SWK": "Sarawak", "TRG": "Terengganu", "WLY": "Wilayah Persekutuan"}
MY_FIX = {"SELURUH NEGERI MELAKA": "Melaka", "Seluruh Negeri Pulau Pinang": "Pulau Pinang", "S.Alam": "Shah Alam",
          "Sg. Siput": "Sungai Siput", "Genting Higlands": "Genting Highlands", "Gemas Johor": "Gemas",
          "Kg Gajah": "Kampung Gajah", "Mukim Chiku": "Chiku", "Jajahan Kecil Lojing": "Lojing",
          "Daerah Rompin": "Rompin", "Grik": "Gerik", "Pulau Aur dan Pulau Pemanggil": "Pulau Aur"}
# Well-known places that sit in a zone without being named in JAKIM's list.
MY_EXTRA = {"SGR01": ["Petaling Jaya", "Subang Jaya", "Kajang", "Ampang", "Cyberjaya"],
            "PNG01": ["George Town", "Butterworth", "Bukit Mertajam"], "KDH01": ["Alor Setar"],
            "KDH02": ["Sungai Petani"], "SBH04": ["Tawau"], "SBH01": ["Sandakan"], "SWK04": [],
            "SGR03": ["Port Klang"]}
# Places GeoNames gets wrong or lacks (approximate centre; used for the qibla only).
MY_COORDS = {"Bukit Tinggi": (3.35, 101.82), "Genting Sempah": (3.37, 101.79), "Janda Baik": (3.33, 101.86),
             "Pulau Tioman": (2.79, 104.17), "Pulau Aur": (2.45, 104.52)}
MY_SKIP = re.compile(r"^(Bahagian|Zon Khas|Puncak Gunung Jerai|Gunung Kinabalu)")


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def read(path):
    return list(csv.reader(open(path, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))


def indonesia(cities):
    groups = {}
    for r in cities:
        if r[8] != "ID" or int(r[14] or 0) < 50000:
            continue
        prov = ID_PROVINCES.get(r[10])
        if not prov:
            continue
        name = ID_FIX.get(r[1], r[1])
        groups.setdefault(prov, []).append({
            "name": name, "slug": slug(name), "lat": round(float(r[4]), 4), "lon": round(float(r[5]), 4),
            "tz": r[17], "elev": int(r[16] or r[15] or 0), "pop": int(r[14]),
        })
    # Same name in two provinces (Depok, Banjar): add the province to the slug of the smaller one.
    seen = {}
    for prov, places in groups.items():
        for p in places:
            seen.setdefault(p["slug"], []).append((p, prov))
    for lst in seen.values():
        if len(lst) > 1:
            lst.sort(key=lambda x: -x[0]["pop"])
            for p, prov in lst[1:]:
                p["slug"] = f"{p['slug']}-{slug(prov)}"
                p["name"] = f"{p['name']} ({prov})"
    out = [{"name": k, "places": sorted(v, key=lambda p: p["slug"])} for k, v in groups.items()]
    for g in out:
        for p in g["places"]:
            del p["pop"]
    return sorted(out, key=lambda g: g["name"])


def malaysia(my_rows, esolat):
    page = open(esolat, encoding="utf-8", errors="replace").read()
    zones = {}
    for z, towns in re.findall(r"value='([A-Z]{3}\d\d)' class='hs'>\1 - ([^<]+)", page):
        zones.setdefault(z, html.unescape(towns).strip())
    # GeoNames state codes, to keep each town inside its own state (Rompin is also in Negeri Sembilan).
    adm1 = {}
    for r in my_rows:
        if r[7] == "ADM1":
            adm1[r[10]] = r[1]
    alias = {"Wilayah Persekutuan": ("Kuala Lumpur", "Labuan", "Putrajaya")}
    index = {}
    for r in my_rows:
        if r[6] in ("P", "A"):
            for n in {r[1], r[2], *r[3].split(",")}:
                if n:
                    index.setdefault(n.strip().lower(), []).append(r)
    groups = {}
    for z, towns in zones.items():
        names = []
        towns = re.sub(r"\([^)]*\)", "", towns)
        for t in re.split(r",\s*", towns):
            t = re.sub(r"\s+", " ", t).strip()
            t = MY_FIX.get(t, t)
            if not t or MY_SKIP.match(t):
                continue
            names.append(t)
        names += MY_EXTRA.get(z, [])
        points = {n: (*MY_COORDS[n], 0) for n in names if n in MY_COORDS}
        for n in names:
            if n in points:
                continue
            want = alias.get(MY_STATES[z[:3]], MY_STATES[z[:3]])
            want = want if isinstance(want, tuple) else (want,)
            cands = [r for r in index.get(n.lower(), []) if r[7].startswith(("PPL", "ADM2"))
                     and any(w.lower() in adm1.get(r[10], "").lower() for w in want)]
            if cands:
                best = max(cands, key=lambda r: int(r[14] or 0))
                points[n] = (float(best[4]), float(best[5]), int(best[16] or best[15] or 0))
        if not points:  # e.g. Genting Sempah: GeoNames has it in another state's district
            for n in names:
                cands = [r for r in index.get(n.lower(), []) if r[7].startswith(("PPL", "ADM2"))]
                if cands:
                    best = max(cands, key=lambda r: int(r[14] or 0))
                    points[n] = (float(best[4]), float(best[5]), int(best[16] or best[15] or 0))
        if not points:
            print(f"zone {z}: no coordinates, skipped", file=sys.stderr)
            continue
        avg = (sum(p[0] for p in points.values()) / len(points), sum(p[1] for p in points.values()) / len(points), 0)
        state = MY_STATES[z[:3]]
        for n in names:
            lat, lon, elev = points.get(n, avg)
            groups.setdefault(state, []).append({"name": n, "slug": slug(n), "lat": round(lat, 4), "lon": round(lon, 4),
                                                 "tz": "Asia/Kuala_Lumpur", "elev": elev, "zone": z})
    out = []
    used = set()
    for state, places in sorted(groups.items()):
        uniq = []
        for p in places:
            if p["slug"] in used:
                continue
            used.add(p["slug"])
            uniq.append(p)
        out.append({"name": state, "places": sorted(uniq, key=lambda p: p["slug"])})
    return out


def main(cities_path, my_path, esolat_path):
    cities = read(cities_path)
    for code, data in (("id", indonesia(cities)), ("my", malaysia(read(my_path), esolat_path))):
        with open(os.path.join(HERE, f"places-{code}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(code, len(data), "groups,", sum(len(g["places"]) for g in data), "places")


if __name__ == "__main__":
    main(*sys.argv[1:4])
