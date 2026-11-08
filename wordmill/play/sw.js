/* Wordmill web: offline after the first visit. Pages and assets: cached copy first, refreshed in the background.
   Day files: network first (they change daily), cached copy when offline. Word lists: cache first. */
var CACHE = "wordmill-play-v1";
var CORE = ["/wordmill/play/app.js", "/wordmill/play/app.css", "/wordmill/play/img/icon-64.png", "/wordmill/play/img/icon-128.png",
            "/wordmill/play/img/appstore.svg"];
self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(CORE); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
function put(req, res) {
  if (res && res.ok) { var copy = res.clone(); caches.open(CACHE).then(function (c) { c.put(req, copy); }); }
  return res;
}
self.addEventListener("fetch", function (e) {
  var req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin || url.pathname.indexOf("/wordmill/play/") !== 0) return;
  if (url.pathname.indexOf("/wordmill/play/data/") === 0) {
    e.respondWith(fetch(req).then(function (r) { return put(req, r); }).catch(function () { return caches.match(req); }));
  } else if (url.pathname.indexOf("/wordmill/play/dict/") === 0) {
    e.respondWith(caches.match(req).then(function (hit) { return hit || fetch(req).then(function (r) { return put(req, r); }); }));
  } else {
    e.respondWith(caches.match(req).then(function (hit) {
      var net = fetch(req).then(function (r) { return put(req, r); });
      return hit || net;
    }));
  }
});
