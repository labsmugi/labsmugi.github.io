"""Builds places-bd.json (Bengali pages), places-ar.json (Arab countries) and places-en.json (Pakistan,
UK, US, Canada, Australia: Pakistanis mostly search "namaz timings" in English) from GeoNames.

Run once by hand, not in the workflow:
    curl -O https://download.geonames.org/export/dump/cities15000.zip && unzip cities15000.zip
    for c in PK BD SA EG AE KW QA BH OM JO IQ MA DZ TN LY SD YE SY LB PS; do
      curl -O https://download.geonames.org/export/dump/alternatenames/$c.zip && unzip $c.zip; done
    python3 prepare_world.py cities15000.txt <folder with the alternatenames txt files>

Each place: name (in the page's language when GeoNames has it), slug (ASCII), coordinates, elevation,
time zone, country and the app's default calculation method for that country (CalcDefaults.method).
Data: GeoNames (CC BY 4.0).
"""
import csv
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

# Same as the app's CalcDefaults.method(for:) and its Hanafi Asr rule for South Asia.
METHOD = {"SA": "ummalqura", "YE": "ummalqura", "OM": "ummalqura", "BH": "ummalqura", "KW": "ummalqura",
          "QA": "ummalqura", "AE": "dubai", "EG": "egypt", "SD": "egypt", "LY": "egypt", "SY": "egypt",
          "LB": "egypt", "IQ": "egypt", "JO": "egypt", "PS": "egypt", "PK": "karachi", "BD": "karachi",
          "US": "isna", "CA": "isna"}
HANAFI = {"PK", "BD"}

AR_COUNTRIES = {"SA": "السعودية", "EG": "مصر", "AE": "الإمارات", "KW": "الكويت", "QA": "قطر", "BH": "البحرين",
                "OM": "عُمان", "JO": "الأردن", "IQ": "العراق", "MA": "المغرب", "DZ": "الجزائر", "TN": "تونس",
                "LY": "ليبيا", "SD": "السودان", "YE": "اليمن", "SY": "سوريا", "LB": "لبنان", "PS": "فلسطين"}
EN_COUNTRIES = {"PK": "Pakistan", "GB": "United Kingdom", "US": "United States", "CA": "Canada", "AU": "Australia"}
# Names GeoNames lacks (or spells oddly) in the page's language.
AR_FIX = {"Kom Ombo": "كوم أمبو", "Unaizah": "عنيزة", "Wad Medani": "ود مدني", "El Eulma": "العلمة", "Temara": "تمارة",
          "Ait Melloul": "أيت ملول", "Berrechid": "برشيد", "Khemisset": "الخميسات", "Inezgane": "إنزكان",
          "Ksar El Kebir": "القصر الكبير", "Taourirt": "تاوريرت", "Bouskoura": "بوسكورة", "Sidi Slimane": "سيدي سليمان",
          "El Kelaa des Srarhna": "قلعة السراغنة", "Dar Bouazza": "دار بوعزة", "Lusail": "لوسيل", "El Mourouj": "المروج",
          "Sakiet ez Zit": "ساقية الزيت", "Sakiet ed Daier": "ساقية الدائر", "Simele": "سميل", "Abu Gharaq": "أبو غرق",
          "El Geneina Fort": "الجنينة", "Dchira El Jihadia": "الدشيرة الجهادية", "سويس": "السويس", "منصورة": "المنصورة",
          "مدينة الإسماعيلية": "الإسماعيلية", "6th of October City": "مدينة 6 أكتوبر",
          "Al Khuşūş": "الخصوص", "Idkū": "إدكو", "Al Ḩawāmidīyah": "الحوامدية", "Sinnūris": "سنورس",
          "Abū al-Kahṣīb": "أبو الخصيب", "Ţūzkhūrmātū": "طوز خورماتو", "Aïn Beïda": "عين البيضاء",
          "Salé Al Jadida": "سلا الجديدة", "Al Fqih Ben Çalah": "الفقيه بن صالح", "Sulţānah": "السلطانة",
          "Al Manāqil": "المناقل", "Qaşr Bin Ghashīr": "قصر بن غشير", "Tājūrā’": "تاجوراء", "Sīdī Ḥusayn": "سيدي حسين",
          "‘Ibrī": "عبري", "Şaḩam": "صحم", "Aş Şuḩār": "صحار", "Şūr": "صور", "ناصر-بوش سابقا": "ناصر",
          "إمارة الشارقة": "الشارقة", "المدينة": "المدينة المنورة", "رَأْس ٱلْخَيْمَة": "رأس الخيمة"}
BN_FIX = {"Thākurgaon": "ঠাকুরগাঁও", "Lalmanirhat": "লালমনিরহাট", "Pallabi": "পল্লবী", "Mirpur Model Thana": "মিরপুর",
          "সাভার উপজেলা": "সাভার", "Kafrul": "কাফরুল", "Bhatara": "ভাটারা", "Narsingdi": "নরসিংদী", "Demra": "ডেমরা",
          "Kaliakair": "কালিয়াকৈর", "Nāgarpur": "নাগরপুর", "Narayanganj": "নারায়ণগঞ্জ", "Motijheel": "মতিঝিল",
          "Paltan": "পল্টন", "Tangail": "টাঙ্গাইল", "Ramna Maidan": "রমনা", "Sonārgaon": "সোনারগাঁও",
          "Tungipara": "টুঙ্গিপাড়া", "Gulshan": "গুলশান", "Azimpur": "আজিমপুর", "Kishorganj": "কিশোরগঞ্জ",
          "Madaripur": "মাদারীপুর", "Dhanmondi": "ধানমন্ডি", "Shibganj": "শিবগঞ্জ", "Puthia": "পুঠিয়া",
          "Ishwardi": "ঈশ্বরদী", "Khulna": "খুলনা", "Jashore": "যশোর", "Kushtia": "কুষ্টিয়া", "Ashuganj City": "আশুগঞ্জ",
          "Karnaphuli": "কর্ণফুলী", "Maijdi": "মাইজদী", "Patiya": "পটিয়া", "Khagrachhari": "খাগড়াছড়ি",
          "Patuakhali": "পটুয়াখালী", "Pirojpur": "পিরোজপুর", "Farīdpur": "ফরিদপুর", "Mānikganj": "মানিকগঞ্জ",
          "Pālang": "পালং", "Gopālganj": "গোপালগঞ্জ", "Sunāmganj": "সুনামগঞ্জ", "Maulavi Bāzār": "মৌলভীবাজার",
          "Mohāmmadpur": "মোহাম্মদপুর", "Nātor": "নাটোর", "Nawābganj": "চাঁপাইনবাবগঞ্জ", "Pār Naogaon": "নওগাঁ",
          "Pābna": "পাবনা", "Shāhzādpur": "শাহজাদপুর", "Joypur Hāt": "জয়পুরহাট", "Sātkhira": "সাতক্ষীরা",
          "Hāthazāri": "হাটহাজারী", "Brāhmanbāria": "ব্রাহ্মণবাড়িয়া", "Cox’s Bāzār": "কক্সবাজার",
          "Chāndpur": "চাঁদপুর", "Rāngāmāti": "রাঙ্গামাটি", "Lākshām": "লাকসাম", "Rāipur": "রায়পুর",
          "Sherpur": "শেরপুর", "Sarishābāri": "সরিষাবাড়ী", "Jāmirdia": "জামিরদিয়া", "Habirbāri": "হবিরবাড়ী",
          "লক্ষ্মীপুর জেলা": "লক্ষ্মীপুর", "ভোলা জেলা": "ভোলা",
          "Rāmganj": "রামগঞ্জ", "Bāndarban": "বান্দরবান", "Sandwīp": "সন্দ্বীপ", "Sātkania": "সাতকানিয়া"}
BD_DIVISIONS = {"81": "ঢাকা", "84": "চট্টগ্রাম", "83": "রাজশাহী", "82": "খুলনা", "85": "বরিশাল",
                "86": "সিলেট", "87": "রংপুর", "H": "ময়মনসিংহ"}


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def localized(alt_dir, countries, lang):
    """geonameid -> preferred name in `lang` (preferred names first, then short, then any)."""
    best = {}
    for cc in countries:
        path = os.path.join(alt_dir, f"{cc}.txt")
        if not os.path.exists(path):
            continue
        for r in csv.reader(open(path, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            if r[2] != lang or r[7] == "1" or r[6] == "1":  # skip historic and colloquial names
                continue
            rank = 0 if r[4] == "1" else (1 if r[5] == "1" else 2)
            if r[1] not in best or rank < best[r[1]][0]:
                best[r[1]] = (rank, r[3])
    return {k: v[1] for k, v in best.items()}


def build(cities, countries, min_pop, group_of, names=None, per_country=None, fix=None):
    groups = {}
    for r in cities:
        cc = r[8]
        if cc not in countries:
            continue
        limit = (per_country or {}).get(cc, min_pop)
        if int(r[14] or 0) < limit:
            continue
        if r[7] == "PPLX":  # city districts (Business Bay, Brent ...): the city's page covers them
            continue
        g = group_of(r)
        if g is None:
            continue
        name = (names or {}).get(r[0], r[1])
        name = re.sub("[\u200e\u200f\u064b-\u0652\u0670]", "", name)  # direction marks, Arabic short vowels
        name = (fix or {}).get(name, (fix or {}).get(r[1], name))
        groups.setdefault(g, []).append({
            "name": name, "slug": slug(r[2] or r[1]), "lat": round(float(r[4]), 4), "lon": round(float(r[5]), 4),
            "tz": r[17], "elev": int(r[16] or r[15] or 0), "cc": cc, "method": METHOD.get(cc, "mwl"),
            "hanafi": cc in HANAFI, "pop": int(r[14]),
        })
    # the same place twice under one name (GeoNames duplicates such as New Cairo): keep the bigger one
    for g, places in groups.items():
        places.sort(key=lambda p: -p["pop"])
        keep, names_seen = [], set()
        for p in places:
            if p["name"] not in names_seen:
                names_seen.add(p["name"])
                keep.append(p)
        groups[g] = keep
    # unique slugs inside a locale: the bigger place keeps the plain slug
    seen = {}
    for g, places in groups.items():
        for p in places:
            seen.setdefault(p["slug"], []).append(p)
    for lst in seen.values():
        lst.sort(key=lambda p: -p["pop"])
        for i, p in enumerate(lst[1:], 2):
            p["slug"] = f"{p['slug']}-{p['cc'].lower()}" if p["cc"] != lst[0]["cc"] else f"{p['slug']}-{i}"
    out = []
    for g, places in groups.items():
        places.sort(key=lambda p: -p["pop"])
        for p in places:
            del p["pop"]
        out.append({"name": g, "places": places})
    return out


def main(cities_path, alt_dir):
    cities = list(csv.reader(open(cities_path, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    pop = {}
    for r in cities:
        pop[r[8]] = pop.get(r[8], 0) + int(r[14] or 0)

    bn = localized(alt_dir, ["BD"], "bn")
    bd = build(cities, {"BD"}, 50000, lambda r: BD_DIVISIONS.get(r[10]), bn, fix=BN_FIX)
    ar = localized(alt_dir, list(AR_COUNTRIES), "ar")
    arab = build(cities, set(AR_COUNTRIES), 100000, lambda r: AR_COUNTRIES[r[8]], ar, fix=AR_FIX)
    arab.sort(key=lambda g: -len(g["places"]))
    en = build(cities, set(EN_COUNTRIES), 100000, lambda r: EN_COUNTRIES[r[8]], None, {"US": 250000})
    order = list(EN_COUNTRIES.values())
    en.sort(key=lambda g: order.index(g["name"]))
    for code, data in (("bd", bd), ("ar", arab), ("en", en)):
        with open(os.path.join(HERE, f"places-{code}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        missing = sum(1 for g in data for p in g["places"] if re.search(r"[A-Za-z]", p["name"]))
        print(code, len(data), "groups,", sum(len(g["places"]) for g in data), "places,", missing, "names still in Latin script")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
