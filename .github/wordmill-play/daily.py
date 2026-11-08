#!/usr/bin/env python3
"""Wordmill web: the daily part of the site (Python 3 standard library only).

Runs every day in the Pages repo (.github/workflows/wordmill-play.yml) and once from
iOS/Wordmill/tools/build_web.py. From bundle.bin next to this file it writes, under
<root>/wordmill/play/:

  data/<lang>/<yyyy-mm-dd>.json      today-30 ... today+2 only, lightly obfuscated; older/later files are deleted
  <lang>/<answers>/<yyyy-mm-dd>/     "answers of that day" pages, past days of the window only
  <lang>/<answers>/index.html        list of those pages
  sitemap.xml

bundle.bin is the app's whole puzzle calendar (zlib + xor, so it doesn't read as plain text in the repo;
this is not security). It's built from the app's Resources by build_web.py; rebuild it when the app's
puzzles change.

    python3 .github/wordmill-play/daily.py [--root .] [--today yyyy-mm-dd]

Without --today the day is taken from UTC at the time of the run. The workflow runs at 12:15 UTC, when every
time zone from UTC-12 to UTC+14 has finished the previous day, so an answers page never goes up while
someone can still play that day.
"""
import argparse
import base64
import datetime as dt
import html
import json
import os
import re
import shutil
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = b"wordmill-play"
PAST, FUTURE = 30, 2
MASK = (1 << 64) - 1


# ---------------------------------------------------------------- bundle

def read_bundle(path=os.path.join(HERE, "bundle.bin")):
    raw = open(path, "rb").read()
    data = bytes(b ^ KEY[i % len(KEY)] for i, b in enumerate(raw))
    return json.loads(zlib.decompress(data).decode("utf-8"))


def write_bundle(obj, path=os.path.join(HERE, "bundle.bin")):
    data = zlib.compress(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 9)
    with open(path, "wb") as f:
        f.write(bytes(b ^ KEY[i % len(KEY)] for i, b in enumerate(data)))


# ---------------------------------------------------------------- the app's rules, ported

class SeededRandom:
    """Model/WordBook.swift SeededRandom: FNV-1a seed, xorshift64."""

    def __init__(self, seed):
        h = 0xcbf29ce484222325
        for b in seed.encode("utf-8"):
            h ^= b
            h = (h * 0x100000001b3) & MASK
        self.state = h or 1

    def next(self):
        s = self.state
        s ^= (s << 13) & MASK
        s ^= s >> 7
        s ^= (s << 17) & MASK
        self.state = s
        return s

    def below(self, bound):
        """Swift's RandomNumberGenerator.next(upperBound:) (Lemire, 64-bit)."""
        r = self.next()
        m = r * bound
        low = m & MASK
        if low < bound:
            t = ((1 << 64) - bound) % bound
            while low < t:
                r = self.next()
                m = r * bound
                low = m & MASK
        return m >> 64

    def shuffle(self, items):
        """Swift's MutableCollection.shuffle(using:)."""
        amount, i = len(items), 0
        while amount > 1:
            j = i + self.below(amount)
            amount -= 1
            items[i], items[j] = items[j], items[i]
            i += 1


def lower(lang, ch):
    if lang["code"] == "tr":
        ch = {"I": "ı", "İ": "i"}.get(ch, ch)
    return ch.lower()


def upper(lang, s):
    if lang["code"] == "tr":
        s = s.replace("i", "İ").replace("ı", "I")
    return s.upper()


def game_letter(lang, ch):
    low = lower(lang, ch)
    if len(low) != 1:
        return None
    fold = dict((p[0], p[1]) for p in lang["fold"].split() if len(p) == 2)
    low = fold.get(low, low)
    return low if low in lang["alphabet"] else None


def cipher_setup(lang, day, proverb, reveal=0.25):
    """CipherModel.init: letter → number and the letters given away."""
    rng = SeededRandom("cipher-%s-%d" % (lang["code"], day))
    codes = list(range(1, len(lang["alphabet"]) + 1))
    rng.shuffle(codes)
    numbers = {c: codes[i] for i, c in enumerate(lang["alphabet"])}
    distinct = sorted(set(l for l in (game_letter(lang, c) for c in proverb) if l))
    rng.shuffle(distinct)
    known = distinct[:max(2, int(len(distinct) * reveal))]
    return numbers, sorted(known)


def day_index(date, first):
    return max(0, (date - first).days)


def puzzles(b, code, day):
    """Everything the web game needs for one day, as the app picks it (calendar index = day % length)."""
    L = b["langs"][code]
    lad = L["ladder"][day % len(L["ladder"])]
    letters, targets, bonus, mill = L["mill"][day % len(L["mill"])]
    proverb = L["cipher"][day % len(L["cipher"])]
    numbers, known = cipher_setup(L, day, proverb)
    return {
        "v": 1, "lang": code, "day": day,
        "ladders": [{"s": s, "t": t, "p": p} for s, t, p in lad],
        "mill": {"l": letters, "t": targets, "b": bonus, "m": mill},
        "cipher": {"p": proverb, "n": numbers, "k": known},
    }


def obfuscate(obj, key):
    """Day files: base64(utf-8 json xor key). app.js reverses it; it only keeps answers out of plain sight."""
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    k = key.encode("utf-8")
    return base64.b64encode(bytes(c ^ k[i % len(k)] for i, c in enumerate(raw))).decode("ascii")


# ---------------------------------------------------------------- pages

def esc(s):
    return html.escape(str(s), quote=True)


def long_date(L, d):
    s = L["s"]
    return s["dateFormat"].format(d=d.day, M=s["months"][d.month - 1], y=d.year)


def app_links(b, code):
    return ("https://apps.apple.com/app/id6829465408?ct=web_%s" % code,
            "https://play.google.com/store/apps/details?id=com.mugilabs.wordmill&referrer=utm_source%%3Dweb%%26utm_campaign%%3D%s" % code)


def badges(b, code):
    s = b["langs"][code]["s"]
    ios, play = app_links(b, code)
    return ('<div class="badges"><a href="%s" rel="noopener"><img src="/wordmill/play/img/appstore.svg" width="120" height="40" alt="%s"></a>'
            '<a href="%s" rel="noopener"><img src="/wordmill/play/img/play-%s.png" width="135" height="40" alt="%s"></a></div>') % (
        esc(ios), esc(s["appStoreAlt"]), esc(play), code, esc(s["playAlt"]))


def app_banner(b, code):
    """The "Get the app: leagues, journey, archive" card with both store badges (also used by build_web.py)."""
    s = b["langs"][code]["s"]
    return ('<aside class="appban" id="appban" aria-label="%s"><img src="/wordmill/play/img/icon-128.png" width="56" height="56" alt="" class="appicon">'
            '<div><p class="apptitle">%s %s</p><p class="apppitch">%s</p>%s</div></aside>') % (
        esc(s["getAppShort"]), esc(s["getApp"]), esc(s["appWords"]), esc(s["appPitch"]), badges(b, code))


def head(b, code, title, desc, path, alternates, extra=""):
    base = b["base"]
    alt = "".join('<link rel="alternate" hreflang="%s" href="%s">' % (h, esc(u)) for h, u in alternates)
    return ('<!doctype html>\n<html lang="%s"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><meta name="description" content="%s">'
            '<link rel="canonical" href="%s">%s'
            '<meta name="apple-itunes-app" content="app-id=6829465408">'
            '<meta name="theme-color" content="#F8F4EC">'
            '<meta property="og:type" content="website"><meta property="og:title" content="%s">'
            '<meta property="og:description" content="%s"><meta property="og:url" content="%s">'
            '<meta property="og:image" content="%sog/%s.png"><meta property="og:image:width" content="1200">'
            '<meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">'
            '<link rel="icon" href="/wordmill/play/img/icon.svg" type="image/svg+xml">'
            '<link rel="stylesheet" href="/wordmill/play/app.css">%s</head>') % (
        b["langs"][code]["s"]["htmlLang"], esc(title), esc(desc), esc(base + path), alt, esc(title), esc(desc),
        esc(base + path), base, code, extra)


def footer(b, code):
    s = b["langs"][code]["s"]
    langs = " ".join('<a href="/wordmill/play/%s/" hreflang="%s" lang="%s">%s</a>' % (c, c, b["langs"][c]["s"]["htmlLang"], esc(b["langs"][c]["name"]))
                     for c in b["order"])
    return ('<footer class="foot"><nav class="langs" aria-label="%s">%s</nav><p>'
            '<a href="/wordmill/play/%s/%s/">%s</a> · <a href="/wordmill/play/%s/widget/">%s</a> · '
            '<a href="/wordmill-privacy.html">%s</a></p><p class="credits">%s</p></footer>') % (
        esc(s["languages"]), langs, code, L_slug(b, code), esc(s["answersIndex"]), code, esc(s["widget"]),
        esc(s["privacy"]), esc(s["credits"]))


def L_slug(b, code):
    return b["langs"][code]["slug"]


def answers_page(b, code, date, day, p, window_dates):
    L = b["langs"][code]
    s = L["s"]
    slug = L["slug"]
    ds = date.isoformat()
    path = "%s/%s/%s/" % (code, slug, ds)
    nice = long_date(L, date)
    title = s["answersTitle"].format(n=day + 1, date=nice)
    desc = s["answersDesc"].format(n=day + 1, date=nice)
    alternates = [(b["langs"][c]["s"]["htmlLang"], "%s%s/%s/%s/" % (b["base"], c, b["langs"][c]["slug"], ds)) for c in b["order"]]
    alternates.append(("x-default", "%sen/%s/%s/" % (b["base"], b["langs"]["en"]["slug"], ds)))
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Wordmill", "item": b["base"] + code + "/"},
        {"@type": "ListItem", "position": 2, "name": s["answersIndex"], "item": "%s%s/%s/" % (b["base"], code, slug)},
        {"@type": "ListItem", "position": 3, "name": nice, "item": b["base"] + path}]}
    out = [head(b, code, title, desc, path, alternates,
                '<script type="application/ld+json">%s</script>' % json.dumps(crumbs, ensure_ascii=False))]
    out.append('<body class="page"><main class="doc"><p class="crumbs"><a href="/wordmill/play/%s/">Wordmill</a> › '
               '<a href="/wordmill/play/%s/%s/">%s</a></p>' % (code, code, slug, esc(s["answersIndex"])))
    out.append('<h1>%s</h1><p class="lead">%s</p>' % (esc(title), esc(s["answersIntro"])))
    out.append('<p><a class="pill" href="/wordmill/play/%s/">%s</a></p>' % (code, esc(s["playToday"])))
    out.append('<section><h2>🪜 %s</h2>' % esc(s["Ladder"]))
    for i, lad in enumerate(p["ladders"]):
        steps = len(lad["p"]) - 1
        out.append('<h3>%s: %s → %s</h3><p class="path">%s</p><p class="muted">%s</p>' % (
            esc(s[["Easy", "Medium", "Hard"][i]]), esc(upper(L, lad["s"])), esc(upper(L, lad["t"])),
            " → ".join(esc(upper(L, w)) for w in lad["p"]), esc(s["bestSteps"].format(n=steps))))
    out.append('</section><section><h2>🌀 %s</h2>' % esc(s["Mill"]))
    m = p["mill"]
    out.append('<p class="wheelrow">%s</p>' % "".join('<span class="lt">%s</span>' % esc(upper(L, c)) for c in m["l"]))
    if m["m"]:
        out.append('<p><b>%s:</b> %s</p>' % (esc(s["millWord"]), ", ".join(esc(upper(L, w)) for w in m["m"])))
    out.append('<p><b>%s (%d):</b> %s</p></section>' % (esc(s["words"]), len(m["t"]), ", ".join(esc(upper(L, w)) for w in m["t"])))
    out.append('<section><h2>🔐 %s</h2><blockquote class="proverb">“%s”</blockquote></section>' % (
        esc(s["Proverb"]), esc(p["cipher"]["p"])))
    i = window_dates.index(date)
    nav = []
    if i > 0:
        d = window_dates[i - 1]
        nav.append('<a href="/wordmill/play/%s/%s/%s/">‹ %s</a>' % (code, slug, d.isoformat(), esc(long_date(L, d))))
    if i + 1 < len(window_dates):
        d = window_dates[i + 1]
        nav.append('<a href="/wordmill/play/%s/%s/%s/">%s ›</a>' % (code, slug, d.isoformat(), esc(long_date(L, d))))
    out.append('<nav class="daynav">%s</nav>' % " ".join(nav))
    out.append(app_banner(b, code))
    out.append('</main>%s</body></html>\n' % footer(b, code))
    return "".join(out)


def answers_index(b, code, dates, firsts):
    L = b["langs"][code]
    s = L["s"]
    path = "%s/%s/" % (code, L["slug"])
    alternates = [(b["langs"][c]["s"]["htmlLang"], "%s%s/%s/" % (b["base"], c, b["langs"][c]["slug"])) for c in b["order"]]
    alternates.append(("x-default", "%sen/%s/" % (b["base"], b["langs"]["en"]["slug"])))
    out = [head(b, code, s["answersIndexTitle"], s["answersIndexDesc"], path, alternates)]
    out.append('<body class="page"><main class="doc"><p class="crumbs"><a href="/wordmill/play/%s/">Wordmill</a></p>'
               '<h1>%s</h1><p class="lead">%s</p><p><a class="pill" href="/wordmill/play/%s/">%s</a></p><ul class="days">' % (
                   code, esc(s["answersIndexTitle"]), esc(s["answersIndexDesc"]), code, esc(s["playToday"])))
    for d in reversed(dates):
        out.append('<li><a href="/wordmill/play/%s/%s/%s/">%s</a> <span class="muted">#%d</span></li>' % (
            code, L["slug"], d.isoformat(), esc(s["answersTitle"].format(n=firsts[d] + 1, date=long_date(L, d))), firsts[d] + 1))
    out.append('</ul>%s</main>%s</body></html>\n' % (app_banner(b, code), footer(b, code)))
    return "".join(out)


def sitemap(b, past_dates):
    base = b["base"]
    order = b["order"]
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    def url(loc, alts, lastmod=None, freq=None):
        rows.append("<url><loc>%s</loc>%s%s%s</url>" % (
            esc(loc), "<lastmod>%s</lastmod>" % lastmod if lastmod else "",
            "<changefreq>%s</changefreq>" % freq if freq else "",
            "".join('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (h, esc(u)) for h, u in alts)))

    def group(make, lastmod=None, freq=None):
        alts = [(b["langs"][c]["s"]["htmlLang"], make(c)) for c in order] + [("x-default", make(None))]
        for c in order:
            url(make(c), alts, lastmod, freq)

    today = past_dates[-1] + dt.timedelta(days=1) if past_dates else None
    url(base, [], today.isoformat() if today else None, "daily")
    group(lambda c: base + ("%s/" % c if c else ""), today.isoformat() if today else None, "daily")
    group(lambda c: "%s%s/%s/" % (base, c or "en", b["langs"][c or "en"]["slug"]), today.isoformat() if today else None, "daily")
    group(lambda c: "%s%s/widget/" % (base, c or "en"), None, "monthly")
    for d in past_dates:  # hreflang for these is in the pages themselves; listing it here too would triple the file
        for c in order:
            url("%s%s/%s/%s/" % (base, c, b["langs"][c]["slug"], d.isoformat()), [], d.isoformat(), "never")
    rows.append("</urlset>")
    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------- run

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and open(path, encoding="utf-8").read() == text:
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run(root, today, b=None):
    b = b or read_bundle()
    play = os.path.join(root, "wordmill", "play")
    first = dt.date.fromisoformat(b["firstDay"])
    window = [today + dt.timedelta(days=k) for k in range(-PAST, FUTURE + 1)]
    window = [d for d in window if d >= first]
    past = [d for d in window if d < today]
    days = {d: day_index(d, first) for d in window}
    for code in b["order"]:
        L = b["langs"][code]
        ddir = os.path.join(play, "data", code)
        keep = set()
        for d in window:
            name = d.isoformat() + ".json"
            keep.add(name)
            p = puzzles(b, code, days[d])
            write(os.path.join(ddir, name), json.dumps({"d": obfuscate(p, "wm" + d.isoformat() + code)}) + "\n")
            if d < today:
                write(os.path.join(play, code, L["slug"], d.isoformat(), "index.html"),
                      answers_page(b, code, d, days[d], p, past))
        for name in os.listdir(ddir):
            if name not in keep:
                os.remove(os.path.join(ddir, name))
        adir = os.path.join(play, code, L["slug"])
        os.makedirs(adir, exist_ok=True)
        for name in os.listdir(adir):
            if re.match(r"^\d{4}-\d{2}-\d{2}$", name) and dt.date.fromisoformat(name) not in past:
                shutil.rmtree(os.path.join(adir, name))
        write(os.path.join(adir, "index.html"), answers_index(b, code, past, days))
    write(os.path.join(play, "sitemap.xml"), sitemap(b, past))
    return window


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.abspath(os.path.join(HERE, "..", "..")))
    ap.add_argument("--today", help="yyyy-mm-dd (default: UTC today)")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(dt.timezone.utc).date()
    window = run(a.root, today)
    print("Wordmill web: %s … %s written under %s" % (window[0], window[-1], os.path.join(a.root, "wordmill", "play")))


if __name__ == "__main__":
    sys.exit(main())
