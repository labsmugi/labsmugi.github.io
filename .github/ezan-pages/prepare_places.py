"""Builds places-tr.json (81 provinces and their districts with coordinates) from GeoNames.

Run once by hand, not in the workflow:
    curl -O https://download.geonames.org/export/dump/TR.zip && unzip TR.zip
    python3 prepare_places.py TR.txt > places-tr.json

Data: GeoNames (https://www.geonames.org), CC BY 4.0. Province pages use the provincial capital;
district pages use the district's town centre when GeoNames has a town of that name within 40 km
of the district, otherwise the district's own point.
"""
import csv
import json
import math
import sys

TR_ASCII = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")


def slug(name):
    s = name.translate(TR_ASCII).lower()
    out, dash = [], False
    for ch in s:
        if ch.isalnum():
            out.append(ch)
            dash = False
        elif not dash:
            out.append("-")
            dash = True
    return "".join(out).strip("-")


# GeoNames spells some districts in ASCII or with old forms; these are the official names.
FIX = {
    "Beypazari": "Beypazarı", "Incesu": "İncesu", "Yahyali": "Yahyalı", "Yesilhisar": "Yeşilhisar",
    "Selcuklu": "Selçuklu", "Ulukisla": "Ulukışla", "Cihanbeyli District": "Cihanbeyli",
    "Şebin Karahisar": "Şebinkarahisar", "Muradiye / Berkri": "Muradiye", "Şemdinni": "Şemdinli",
    "Lâpseki": "Lapseki", "Lâlapaşa": "Lalapaşa", "Şarkîkaraağaç": "Şarkikaraağaç",
}
# Not a district of its own (GeoNames' name for Hakkari's central district).
SKIP = {"Doski Aşireti Bölgesi"}


def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def main(path):
    rows = list(csv.reader(open(path, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    adm1 = {r[10]: r for r in rows if r[7] == "ADM1"}
    capitals = {r[10]: r for r in rows if r[7] in ("PPLA", "PPLC")}
    towns = {}
    for r in rows:
        if r[6] == "P":
            towns.setdefault((r[10], tr_lower(r[1])), []).append(r)

    provinces = []
    for code, a in adm1.items():
        name = a[1].replace("Elâzığ", "Elazığ")
        cap = capitals.get(code, a)
        prov = {"name": name, "slug": slug(name), "lat": round(float(cap[4]), 4), "lon": round(float(cap[5]), 4), "districts": []}
        for r in rows:
            if r[7] != "ADM2" or r[10] != code:
                continue
            raw = r[1].removesuffix(" İlçesi").removesuffix(" Merkez").strip()
            if raw in SKIP:
                continue
            dname = FIX.get(raw, raw)
            # The central district carries the province's name: the province page covers it.
            if slug(dname) == slug(name) or dname == "Merkez":
                continue
            point = (float(r[4]), float(r[5]))
            best = None
            for t in towns.get((code, tr_lower(dname)), []) + towns.get((code, tr_lower(raw)), []):
                p = (float(t[4]), float(t[5]))
                d = km(point, p)
                if d <= 40 and (best is None or d < best[0]):
                    best = (d, p)
            lat, lon = best[1] if best else point
            prov["districts"].append({"name": dname, "slug": slug(dname), "lat": round(lat, 4), "lon": round(lon, 4)})
        prov["districts"].sort(key=lambda d: d["slug"])
        provinces.append(prov)
    provinces.sort(key=lambda p: p["slug"])
    json.dump(provinces, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
