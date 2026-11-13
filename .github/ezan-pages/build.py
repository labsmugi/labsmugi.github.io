"""Ezan Vakti web pages: prayer times for Turkey's 81 provinces and 922 districts, plus other
countries in their own languages (intl.py: ezan/id/ Indonesia, ezan/ms/ Malaysia).

Writes, under <root>/ezan/:
  index.html                                   all provinces
  <il>/index.html, <il>/<ilce>/index.html      this month's times, qibla, links
  <il>/ramazan-imsakiyesi-2027/index.html      Ramadan 2027 (also per district)
  ramazan-imsakiyesi-2027/index.html           all provinces' Ramadan pages
  sitemap.xml

Pages only change when the month changes, so the daily workflow commits about once a month; today's
row, the "next prayer" countdown and the hero card are filled in by ezan/app.js in the browser.
Times come from prayertimes.py, a port of the app's calculator (Diyanet method). Standard library only.

    python3 .github/ezan-pages/build.py --root .            # today in Turkey
    python3 .github/ezan-pages/build.py --root . --today 2027-02-01
"""
import argparse
import calendar
import html
import json
import math
import os
import shutil
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from prayertimes import NAMES, hhmm, times  # noqa: E402
import intl  # noqa: E402

SITE = "https://labsmugi.github.io"
BASE = "/ezan/"
TZ = "Europe/Istanbul"
APP_STORE = "https://apps.apple.com/tr/app/id6825951256"
PLAY = "https://play.google.com/store/apps/details?id=com.mugilabs.ezan&hl=tr"

# Ramadan 1448 (Diyanet / Umm al-Qura, same as the app): 1 Ramazan = 8 Feb 2027, 29 days, Bayram 9 Mar.
RAMADAN_YEAR = 2027
RAMADAN_START = date(2027, 2, 8)
RAMADAN_DAYS = 29
KADIR_EVENING = date(2027, 3, 5)  # evening before 27 Ramazan
BAYRAM = date(2027, 3, 9)
RAMADAN_SLUG = f"ramazan-imsakiyesi-{RAMADAN_YEAR}"

MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
WEEKDAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
WEEKDAYS_SHORT = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
LABELS = {"imsak": "İmsak", "gunes": "Güneş", "ogle": "Öğle", "ikindi": "İkindi", "aksam": "Akşam", "yatsi": "Yatsı"}
TR_ORDER = "abcçdefgğhıijklmnoöprsştuüvyz"


def tr_key(name):
    s = name.replace("I", "ı").replace("İ", "i").lower().replace("â", "a").replace("î", "i").replace("û", "u")
    return [TR_ORDER.index(c) if c in TR_ORDER else 100 + ord(c) for c in s]


def e(s):
    return html.escape(str(s), quote=True)


def long_date(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year} {WEEKDAYS[d.weekday()]}"


def qibla(lat, lon):
    """Bearing (° from north) and distance (km) to the Kaaba, as in the app's Geo.swift."""
    k_lat, k_lon = math.radians(21.4225), math.radians(39.8262)
    la, lo = math.radians(lat), math.radians(lon)
    d_lon = k_lon - lo
    y = math.sin(d_lon) * math.cos(k_lat)
    x = math.cos(la) * math.sin(k_lat) - math.sin(la) * math.cos(k_lat) * math.cos(d_lon)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    h = math.sin((k_lat - la) / 2) ** 2 + math.cos(la) * math.cos(k_lat) * math.sin(d_lon / 2) ** 2
    return bearing, 6371 * 2 * math.asin(math.sqrt(h))


def compass(bearing):
    names = ["kuzey", "kuzeydoğu", "doğu", "güneydoğu", "güney", "güneybatı", "batı", "kuzeybatı"]
    return names[int((bearing + 22.5) // 45) % 8]


def day_times(d, lat, lon):
    t = times(d, lat, lon, TZ, "diyanet")
    return [hhmm(t[n]) for n in NAMES]


# ---------------------------------------------------------------- page parts

def page(path, title, description, body, crumbs, today_iso=None, extra_head=""):
    url = SITE + path
    crumb_ld = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + href}
            for i, (name, href) in enumerate(crumbs)
        ],
    }
    nav = " › ".join(
        f'<a href="{e(href)}">{e(name)}</a>' if i < len(crumbs) - 1 else f"<span>{e(name)}</span>"
        for i, (name, href) in enumerate(crumbs)
    )
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(url)}">
<meta name="apple-itunes-app" content="app-id=6825951256">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{SITE}/img/ezan-vakti.png">
<meta property="og:locale" content="tr_TR">
<meta name="theme-color" content="#1c876b">
<link rel="icon" href="/img/ezan-vakti.png">
<link rel="stylesheet" href="{BASE}site.css">
<script type="application/ld+json">{json.dumps(crumb_ld, ensure_ascii=False)}</script>{extra_head}
</head>
<body{f' data-built="{today_iso}"' if today_iso else ''}>
<header class="top"><div class="wrap"><a class="logo" href="{BASE}"><img src="/img/ezan-vakti.png" alt="" width="28" height="28">Ezan Vakti</a></div></header>
<main class="wrap">
<nav class="crumbs">{nav}</nav>
{body}
{app_card()}
</main>
<footer class="wrap foot">
<p>Vakitler, Diyanet İşleri Başkanlığı'nın kullandığı usulle (imsak 18°, yatsı 17°, temkin payları) hesaplanır. Resmî takvimle karşılaştırıldığında vakitlerin büyük çoğunluğu aynı dakikadır, kalanlarda en fazla 1 dakika fark olur; ihtiyat için vaktin girmesini birkaç dakika bekleyin.</p>
<p><a href="{BASE}">Tüm iller</a> · <a href="{BASE}{RAMADAN_SLUG}/">Ramazan İmsakiyesi {RAMADAN_YEAR}</a> · <a href="/">MuGi Labs</a> · <a href="/privacy.html">Gizlilik</a></p>
<p class="small">Konum verisi: <a href="https://www.geonames.org/" rel="nofollow">GeoNames</a> (CC BY 4.0).</p>
</footer>
<script src="{BASE}app.js" defer></script>
</body>
</html>
"""


def app_card():
    return f"""<section class="app">
<img src="/img/ezan-vakti.png" alt="Ezan Vakti uygulama simgesi" width="64" height="64" loading="lazy">
<div>
<h2>Ezan vaktinde bildirim alın</h2>
<p>Ezan Vakti uygulaması bulunduğunuz yerin vakitlerini internetsiz hesaplar, ezan sesiyle hatırlatır; kıble pusulası, Kur'an-ı Kerîm, imsakiye ve sahur hatırlatıcısı da içinde. Reklamsız ve ücretsiz.</p>
<p class="stores"><a class="store" href="{APP_STORE}">App Store</a><a class="store" href="{PLAY}">Google Play</a></p>
</div>
</section>"""


def times_table(rows, highlight_dates=True, ramadan=False):
    head = "".join(f"<th>{LABELS[n]}</th>" for n in NAMES)
    if ramadan:
        head = head.replace("<th>İmsak</th>", "<th>İmsak<br><small>sahur sonu</small></th>").replace(
            "<th>Akşam</th>", "<th>Akşam<br><small>iftar</small></th>")
    first = "<th>Gün</th><th>Tarih</th>" if ramadan else "<th>Tarih</th>"
    out = [f'<div class="tablewrap"><table class="times{" ramadan" if ramadan else ""}"><thead><tr>{first}{head}</tr></thead><tbody>']
    for row in rows:
        d, ts = row["date"], row["times"]
        cls = row.get("cls", "")
        note = f'<span class="note">{e(row["note"])}</span>' if row.get("note") else ""
        label = f"{d.day} {MONTHS[d.month - 1][:3]} {WEEKDAYS_SHORT[d.weekday()]}"
        lead = f'<td class="rd">{e(row["rday"])}</td>' if ramadan else ""
        cells = "".join(f"<td>{t}</td>" for t in ts)
        out.append(f'<tr data-d="{d.isoformat()}" data-t="{" ".join(ts)}"{f" class={cls}" if cls else ""}>{lead}<td class="d">{label}{note}</td>{cells}</tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def hero(name, d, ts):
    cells = "".join(
        f'<li data-n="{"sun" if n == "gunes" else n}"><span>{LABELS[n]}</span><b>{t}</b></li>' for n, t in zip(NAMES, ts)
    )
    return f"""<section class="hero" id="hero">
<p class="today"><span id="hero-date">{e(long_date(d))}</span> · {e(name)}</p>
<p class="next" id="next" hidden></p>
<ul class="six">{cells}</ul>
</section>"""


def month_rows(lat, lon, first):
    last = calendar.monthrange(first.year, first.month)[1]
    rows = [{"date": first + timedelta(days=i), "times": day_times(first + timedelta(days=i), lat, lon)} for i in range(last)]
    return rows


def next_day_attr(lat, lon, first):
    """Times of the 1st of next month (lets app.js count down to tomorrow's imsak on the last day)."""
    nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return f'<div hidden id="after" data-d="{nxt.isoformat()}" data-t="{" ".join(day_times(nxt, lat, lon))}"></div>'


def ramadan_rows(lat, lon):
    rows = []
    for i in range(RAMADAN_DAYS + 1):
        d = RAMADAN_START + timedelta(days=i)
        note, cls, rday = "", "", str(i + 1)
        if d == RAMADAN_START:
            note = "İlk oruç"
        if d == KADIR_EVENING:
            note, cls = "Kadir Gecesi (akşam)", "kadir"
        if d == BAYRAM - timedelta(days=1):
            note = "Arefe"
        if d == BAYRAM:
            note, cls, rday = "Ramazan Bayramı", "bayram", "–"
        rows.append({"date": d, "times": day_times(d, lat, lon), "note": note, "cls": cls, "rday": rday})
    return rows


# ---------------------------------------------------------------- pages

def place_page(p, prov, siblings, first, today):
    """Province page when prov is None, otherwise a district page of province prov."""
    is_prov = prov is None
    name = p["name"]
    full = name if is_prov else f"{name}, {prov['name']}"
    path = f"{BASE}{p['slug']}/" if is_prov else f"{BASE}{prov['slug']}/{p['slug']}/"
    month = f"{MONTHS[first.month - 1]} {first.year}"
    rows = month_rows(p["lat"], p["lon"], first)
    hero_row = next((r for r in rows if r["date"] == today), rows[0])
    bearing, dist = qibla(p["lat"], p["lon"])
    t0 = hero_row["times"]
    title = f"{name} Namaz Vakitleri – {name} Ezan Vakti ({month})"
    if not is_prov:
        title = f"{name} Namaz Vakitleri – {name} ({prov['name']}) Ezan Vakti ({month})"
    desc = (f"{full} ezan vakitleri: imsak, güneş, öğle, ikindi, akşam ve yatsı saatleri. "
            f"{month} aylık namaz vakitleri tablosu, kıble yönü ve Ramazan {RAMADAN_YEAR} imsakiyesi.")
    crumbs = [("Namaz Vakitleri", BASE)]
    if is_prov:
        crumbs.append((name, path))
    else:
        crumbs += [(prov["name"], f"{BASE}{prov['slug']}/"), (name, path)]

    links = ""
    if is_prov and p["districts"]:
        items = "".join(f'<li><a href="{BASE}{p["slug"]}/{d["slug"]}/">{e(d["name"])}</a></li>'
                        for d in sorted(p["districts"], key=lambda d: tr_key(d["name"])))
        links = f'<section><h2>{e(name)} ilçeleri namaz vakitleri</h2><ul class="grid">{items}</ul></section>'
    elif not is_prov:
        items = "".join(f'<li><a href="{BASE}{prov["slug"]}/{d["slug"]}/">{e(d["name"])}</a></li>'
                        for d in sorted(siblings, key=lambda d: tr_key(d["name"])) if d["slug"] != p["slug"])
        links = (f'<section><h2>{e(prov["name"])} ve ilçeleri</h2><ul class="grid">'
                 f'<li><a href="{BASE}{prov["slug"]}/"><b>{e(prov["name"])} merkez</b></a></li>{items}</ul></section>')

    body = f"""<h1>{e(name)} Namaz Vakitleri</h1>
<p class="lead">{e(full)} için ezan vakitleri. Bugünün vakitleri ve bir sonraki namaza kalan süre aşağıda; ayın tamamı tabloda.</p>
{hero(full, hero_row["date"], t0)}
<p class="cta"><a class="btn" href="{path}{RAMADAN_SLUG}/">{e(name)} Ramazan İmsakiyesi {RAMADAN_YEAR} →</a></p>
<section><h2>{e(name)} {month} namaz vakitleri</h2>
{times_table(rows)}{next_day_attr(p["lat"], p["lon"], first)}
</section>
<section class="info"><h2>{e(name)} kıble yönü</h2>
<p>{e(full)} için kıble, kuzeyden saat yönünde <b>{bearing:.0f}°</b> ({compass(bearing)} yönü). Kâbe'ye kuş uçuşu uzaklık yaklaşık <b>{dist:,.0f} km</b>.</p>
</section>
{links}"""
    return path, page(path, title, desc, body, crumbs, today.isoformat())


def ramadan_page(p, prov, today):
    is_prov = prov is None
    name = p["name"]
    full = name if is_prov else f"{name}, {prov['name']}"
    place_path = f"{BASE}{p['slug']}/" if is_prov else f"{BASE}{prov['slug']}/{p['slug']}/"
    path = f"{place_path}{RAMADAN_SLUG}/"
    rows = ramadan_rows(p["lat"], p["lon"])
    first, last = rows[0]["times"], rows[RAMADAN_DAYS - 1]["times"]
    title = f"{name} İmsakiye {RAMADAN_YEAR} – {name} Ramazan İmsakiyesi, Sahur ve İftar Saatleri"
    if not is_prov:
        title = f"{name} ({prov['name']}) İmsakiye {RAMADAN_YEAR} – Sahur ve İftar Saatleri"
    desc = (f"{full} Ramazan {RAMADAN_YEAR} imsakiyesi: 8 Şubat – 8 Mart {RAMADAN_YEAR} arası her gün sahur (imsak) ve iftar "
            f"(akşam) saatleri. İlk gün sahur {first[0]}, iftar {first[4]}.")
    crumbs = [("Namaz Vakitleri", BASE)]
    if not is_prov:
        crumbs.append((prov["name"], f"{BASE}{prov['slug']}/"))
    crumbs += [(name, place_path), (f"İmsakiye {RAMADAN_YEAR}", path)]
    body = f"""<h1>{e(name)} Ramazan İmsakiyesi {RAMADAN_YEAR}</h1>
<p class="lead">{e(full)} için {RAMADAN_YEAR} Ramazan ayı sahur ve iftar saatleri. Ramazan 8 Şubat {RAMADAN_YEAR} Pazartesi başlıyor
(ilk sahur 7'yi 8'e bağlayan gece), Kadir Gecesi 5 Mart akşamı, Ramazan Bayramı 9 Mart {RAMADAN_YEAR} Salı.</p>
<ul class="facts">
<li><span>İlk sahur bitişi</span><b>{first[0]}</b></li>
<li><span>İlk iftar</span><b>{first[4]}</b></li>
<li><span>Son iftar ({rows[RAMADAN_DAYS - 1]["date"].day} Mart)</span><b>{last[4]}</b></li>
</ul>
{times_table(rows, ramadan=True)}
<section class="info"><h2>İmsakiye nasıl okunur?</h2>
<p><b>İmsak</b> sütunu sahurun bittiği, orucun başladığı saattir; yemeyi birkaç dakika önce bırakmak ihtiyatlıdır.
<b>Akşam</b> sütunu iftar saatidir. Teravih namazı yatsı namazından sonra kılınır.</p>
<p><a href="{place_path}">{e(name)} günlük namaz vakitleri →</a></p>
</section>"""
    return path, page(path, title, desc, body, crumbs, today.isoformat())


def index_page(provinces, today):
    path = BASE
    items = "".join(f'<li><a href="{BASE}{p["slug"]}/">{e(p["name"])}</a></li>'
                    for p in sorted(provinces, key=lambda p: tr_key(p["name"])))
    body = f"""<h1>Namaz Vakitleri</h1>
<p class="lead">Türkiye'nin 81 ili ve 922 ilçesi için ezan vakitleri, aylık namaz vakitleri tablosu, kıble yönü ve Ramazan {RAMADAN_YEAR} imsakiyesi. İlinizi seçin.</p>
<p class="cta"><a class="btn" href="{BASE}{RAMADAN_SLUG}/">Ramazan İmsakiyesi {RAMADAN_YEAR} →</a></p>
<ul class="grid big">{items}</ul>"""
    title = "Namaz Vakitleri – 81 İl ve İlçe Ezan Vakitleri | Ezan Vakti"
    desc = "Türkiye'nin tüm il ve ilçeleri için ezan vakitleri: imsak, güneş, öğle, ikindi, akşam, yatsı. Aylık tablo, kıble yönü ve Ramazan imsakiyesi."
    return path, page(path, title, desc, body, [("Namaz Vakitleri", BASE)], today.isoformat())


def ramadan_index(provinces, today):
    path = f"{BASE}{RAMADAN_SLUG}/"
    items = "".join(f'<li><a href="{BASE}{p["slug"]}/{RAMADAN_SLUG}/">{e(p["name"])}</a></li>'
                    for p in sorted(provinces, key=lambda p: tr_key(p["name"])))
    body = f"""<h1>Ramazan İmsakiyesi {RAMADAN_YEAR}</h1>
<p class="lead">{RAMADAN_YEAR} Ramazan ayı 8 Şubat Pazartesi başlıyor, 8 Mart'ta son oruç tutuluyor; Ramazan Bayramı 9 Mart Salı.
Kadir Gecesi 5 Mart akşamı. İlinizi seçin, sahur ve iftar saatlerini görün; il sayfalarından ilçenize geçebilirsiniz.</p>
<ul class="grid big">{items}</ul>"""
    title = f"Ramazan İmsakiyesi {RAMADAN_YEAR} – 81 İl Sahur ve İftar Saatleri"
    desc = f"{RAMADAN_YEAR} Ramazan imsakiyesi: Türkiye'nin 81 ili ve ilçeleri için sahur (imsak) ve iftar saatleri. Ramazan 8 Şubat'ta başlıyor."
    crumbs = [("Namaz Vakitleri", BASE), (f"İmsakiye {RAMADAN_YEAR}", path)]
    return path, page(path, title, desc, body, crumbs, today.isoformat())


# ---------------------------------------------------------------- output

def write(root, url_path, content):
    path = os.path.join(root, url_path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == content:
                return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def sitemap(paths, lastmod):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in paths:
        out.append(f"<url><loc>{SITE}{p}</loc><lastmod>{lastmod}</lastmod></url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--today", help="YYYY-MM-DD (default: today in Turkey)")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else datetime.now(ZoneInfo(TZ)).date()
    first = today.replace(day=1)
    # Pages carry the build day only in data-built (for app.js); keep it at the 1st so that pages
    # stay byte-identical for the whole month and the workflow has nothing to commit.
    stamp = first

    with open(os.path.join(HERE, "places-tr.json"), encoding="utf-8") as f:
        provinces = json.load(f)

    root = os.path.join(args.root, "ezan")
    wanted = set()
    paths = []

    def emit(result):
        path, content = result
        write(args.root, path, content)
        wanted.add(path.strip("/"))
        paths.append(path)

    emit(index_page(provinces, stamp))
    emit(ramadan_index(provinces, stamp))
    for prov in provinces:
        emit(place_page(prov, None, None, first, stamp))
        emit(ramadan_page(prov, None, stamp))
        for d in prov["districts"]:
            emit(place_page(d, prov, prov["districts"], first, stamp))
            emit(ramadan_page(d, prov, stamp))

    for result in intl.pages(first, stamp):
        emit(result)

    # After Ramadan 2027 is over the imsakiye pages stay up (they keep ranking for next year's
    # queries until RAMADAN_* above is moved to 2028).

    # Remove page folders that are no longer generated (renamed places), never the static assets.
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        rel = os.path.relpath(dirpath, args.root).replace(os.sep, "/")
        if "index.html" in filenames and rel not in wanted:
            os.remove(os.path.join(dirpath, "index.html"))
        if dirpath != root and not os.listdir(dirpath):
            os.rmdir(dirpath)

    sm = sitemap(paths, stamp.isoformat())
    sm_path = os.path.join(root, "sitemap.xml")
    old = open(sm_path, encoding="utf-8").read() if os.path.exists(sm_path) else None
    if old != sm:
        with open(sm_path, "w", encoding="utf-8") as f:
            f.write(sm)
    print(f"{len(paths)} pages for {MONTHS[first.month - 1]} {first.year}")


if __name__ == "__main__":
    main()
