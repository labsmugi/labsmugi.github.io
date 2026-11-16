"""ezan/indir/: one link for every share from the app (share text and the QR code on shared images).

An iPhone/iPad goes to the App Store, an Android phone to Google Play (with the ?s= source passed on as
the Play install referrer, so Play Console's acquisition report shows which share brought the install),
anything else sees both badges. Not indexed and not in the sitemap.
"""

APP_STORE = "https://apps.apple.com/app/id6825951256"
PLAY = "https://play.google.com/store/apps/details?id=com.mugilabs.ezan"
PATH = "/ezan/indir/"

PAGE = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Ezan Vakti uygulamasını indir</title>
<meta name="description" content="Ezan Vakti: namaz vakitleri, Ramazan imsakiyesi, kıble, Kur'an ve zikir. iPhone ve Android için ücretsiz.">
<meta name="apple-itunes-app" content="app-id=6825951256">
<meta property="og:title" content="Ezan Vakti">
<meta property="og:description" content="Namaz vakitleri, Ramazan imsakiyesi, kıble, Kur'an ve zikir. Ücretsiz.">
<link rel="canonical" href="https://labsmugi.github.io/ezan/">
<script>
(function () {
  var ua = navigator.userAgent || "";
  var src = (location.search.match(/[?&]s=([a-z0-9_-]{1,32})/i) || [])[1] || "share";
  var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  if (ios) { location.replace("%(app_store)s"); return; }
  if (/Android/i.test(ua)) {
    location.replace("%(play)s&referrer=" + encodeURIComponent("utm_source=" + src + "&utm_medium=share"));
  }
})();
</script>
<style>
  body { margin: 0; font: 17px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0f3d36; color: #fff; display: flex; min-height: 100vh; align-items: center; justify-content: center; }
  main { max-width: 420px; padding: 32px 24px; text-align: center; }
  h1 { font-size: 28px; margin: 0 0 8px; }
  p { margin: 0 0 24px; opacity: .85; }
  a.btn { display: block; margin: 12px 0; padding: 14px 18px; border-radius: 14px; background: #fff;
          color: #0f3d36; font-weight: 600; text-decoration: none; }
  a.web { color: #fff; opacity: .8; font-size: 15px; }
</style>
</head>
<body>
<main>
  <h1>Ezan Vakti</h1>
  <p id="t">Namaz vakitleri, Ramazan imsakiyesi, kıble, Kur'an ve zikir. Ücretsiz.</p>
  <a class="btn" id="a" href="%(app_store)s">App Store'dan indir (iPhone)</a>
  <a class="btn" id="g" href="%(play)s">Google Play'den indir (Android)</a>
  <p style="margin-top:24px"><a class="web" id="w" href="/ezan/">Namaz vakitlerine web'den bak →</a></p>
</main>
<script>
  // Shares come from every interface language of the app; visitors who don't read Turkish get English.
  if (!/^tr/i.test(navigator.language || "")) {
    document.documentElement.lang = "en";
    document.getElementById("t").textContent = "Prayer times, Ramadan timetable, qibla, Quran and dhikr. Free.";
    document.getElementById("a").textContent = "Download on the App Store (iPhone)";
    document.getElementById("g").textContent = "Get it on Google Play (Android)";
    document.getElementById("w").style.display = "none";
  }
</script>
</body>
</html>
"""


def page():
    return PATH, PAGE % {"app_store": APP_STORE, "play": PLAY}
