// Ezan Vakti web pages: marks today's row and fills the hero card with today's times and a
// countdown to the next prayer. Times are local to Turkey (Europe/Istanbul), as on the pages.
(function () {
  var NAMES = ["İmsak", "Güneş", "Öğle", "İkindi", "Akşam", "Yatsı"];
  function nowInTurkey() {
    var parts = {};
    new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Istanbul", year: "numeric", month: "2-digit",
      day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" })
      .formatToParts(new Date()).forEach(function (p) { parts[p.type] = p.value; });
    return { day: parts.year + "-" + parts.month + "-" + parts.day,
             secs: (+parts.hour) * 3600 + (+parts.minute) * 60 + (+parts.second) };
  }
  function toSecs(hm) { var p = hm.split(":"); return (+p[0]) * 3600 + (+p[1]) * 60; }
  function nextDay(iso) {
    var d = new Date(iso + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + 1);
    return d.toISOString().slice(0, 10);
  }
  function rowFor(iso) { return document.querySelector('[data-d="' + iso + '"][data-t]'); }
  function longDate(iso) {
    try {
      return new Intl.DateTimeFormat("tr-TR", { timeZone: "UTC", day: "numeric", month: "long", year: "numeric", weekday: "long" })
        .format(new Date(iso + "T12:00:00Z"));
    } catch (e) { return iso; }
  }
  function tick() {
    var now = nowInTurkey();
    var row = rowFor(now.day);
    document.querySelectorAll("tr.today").forEach(function (r) { r.classList.remove("today"); });
    if (row && row.tagName === "TR") row.classList.add("today");
    var hero = document.getElementById("hero");
    if (!hero || !row) return;
    var t = row.getAttribute("data-t").split(" ");
    var items = hero.querySelectorAll(".six li");
    var current = -1, next = -1;
    t.forEach(function (hm, i) {
      items[i].querySelector("b").textContent = hm;
      if (toSecs(hm) <= now.secs) current = i; else if (next < 0) next = i;
    });
    items.forEach(function (li, i) { li.classList.toggle("now", i === current && current !== 1); });
    document.getElementById("hero-date").textContent = longDate(now.day);
    var left, label;
    if (next >= 0) { left = toSecs(t[next]) - now.secs; label = NAMES[next]; }
    else {
      var tomorrow = rowFor(nextDay(now.day));
      if (!tomorrow) return;
      left = 86400 - now.secs + toSecs(tomorrow.getAttribute("data-t").split(" ")[0]); label = "İmsak";
    }
    var h = Math.floor(left / 3600), m = Math.floor((left % 3600) / 60);
    var el = document.getElementById("next");
    el.textContent = label + " vaktine " + (h ? h + " sa " : "") + m + " dk";
    el.hidden = false;
  }
  tick();
  setInterval(tick, 20000);
})();
