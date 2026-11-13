"""Compares the pages' Diyanet times with namazvakitleri.diyanet.gov.tr for a sample of places.

    python3 .github/ezan-pages/check_diyanet.py [N]     # N random districts (default 12) + 5 provinces

Run by hand after changing prayertimes.py; not part of the workflow. Prints, per place, how many
days match to the minute and the largest difference.
"""
import json
import os
import random
import re
import sys
import time
import urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from prayertimes import NAMES, hhmm, times  # noqa: E402

SITE = "https://namazvakitleri.diyanet.gov.tr"
MONTHS = {m: i + 1 for i, m in enumerate("Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık".split())}
UP = str.maketrans("abcçdefgğhıijklmnoöprsştuüvyzâîû", "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZAİU")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ezan-vakti check script)"})
    return urllib.request.urlopen(req, timeout=30).read().decode()


def regions(change, **kw):
    q = "&".join(f"{k}={v}" for k, v in kw.items())
    return json.loads(get(f"{SITE}/tr-TR/home/GetRegList?ChangeType={change}&CountryId=2&Culture=tr-TR&{q}"))


def diyanet_rows(path):
    html = get(SITE + path)
    rows = re.findall(r"<td>(\d+) (\w+) (\d{4}) \w+</td>\s*<td>[^<]*</td>((?:\s*<td>\d\d:\d\d</td>){6})", html)
    return {date(int(y), MONTHS[m], int(d)): re.findall(r"\d\d:\d\d", ts) for d, m, y, ts in rows}


def minutes(hm):
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    provinces = json.load(open(os.path.join(HERE, "places-tr.json"), encoding="utf-8"))
    rnd = random.Random(7)
    sample = [(p, None) for p in rnd.sample(provinces, 5)]
    districts = [(d, p) for p in provinces for d in p["districts"]]
    sample += rnd.sample(districts, n)
    states = {s["SehirAdi"]: s["SehirID"] for s in regions("country")["StateList"]}
    total = exact = 0
    for place, prov in sample:
        il = (prov or place)["name"].translate(UP)
        target = place["name"].translate(UP)
        lst = regions("state", StateId=states[il])["StateRegionList"]
        match = [r for r in lst if r["IlceAdi"] == target]
        if not match:
            print(f"? {place['name']}: not on Diyanet's list")
            continue
        rows = diyanet_rows(match[0]["IlceUrl"])
        worst, ok = 0, 0
        for day, ts in rows.items():
            mine = times(day, place["lat"], place["lon"], "Europe/Istanbul", "diyanet")
            diffs = [minutes(hhmm(mine[k])) - minutes(t) for k, t in zip(NAMES, ts)]
            ok += sum(1 for x in diffs if x == 0)
            worst = max([worst] + [abs(x) for x in diffs])
        cnt = len(rows) * 6
        total += cnt
        exact += ok
        label = place["name"] + (f" ({prov['name']})" if prov else "")
        print(f"{label:32s} {ok / cnt:6.1%} exact, worst {worst} min, {len(rows)} days")
        time.sleep(0.5)
    print(f"overall {exact / total:.1%} of {total} times exact")


if __name__ == "__main__":
    main()
