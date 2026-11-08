/* Wordmill web game. The rules are ports of the iOS app (Games/*Model.swift, Model/Share.swift, Model/DayScore.swift):
   same puzzles on the same day, same stars, same spoiler-free share text. Progress stays in localStorage only. */
(function () {
  "use strict";
  var C = JSON.parse(document.getElementById("cfg").textContent);
  var T = C.t, LANG = C.lang, LOC = C.htmlLang, EMBED = C.mode === "embed";
  var $ = function (id) { return document.getElementById(id); };
  var plural = new Intl.PluralRules(LOC);

  // ---------------------------------------------------------------- text
  function t(key) {
    var args = Array.prototype.slice.call(arguments, 1), v = T[key] == null ? key : T[key], i = 0;
    if (typeof v === "object") {
      var n = args.filter(function (a) { return typeof a === "number"; })[0];
      v = v[plural.select(n)] || v.other;
    }
    return v.replace(/%(\d+)\$(?:lld|@|d)|%(?:lld|@|d)/g, function (m, pos) {
      return String(pos ? args[pos - 1] : args[i++]);
    });
  }
  function up(s) { return s.toLocaleUpperCase(LOC); }
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) {
      if (k === "text") e.textContent = attrs[k];
      else if (k === "html") e.innerHTML = attrs[k];
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] === true) e.setAttribute(k, "");
      else if (attrs[k] !== false && attrs[k] != null) e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  var FOLD = {};
  C.fold.split(" ").forEach(function (p) { var a = Array.from(p); if (a.length === 2) FOLD[a[0]] = a[1]; });
  /** PuzzleLanguage.gameLetter: lowercase, fold (é → e), nil if not a letter of the language. */
  function gameLetter(ch) {
    var low = ch.toLocaleLowerCase(LOC);
    if (Array.from(low).length !== 1) return null;
    low = FOLD[low] || low;
    return C.alphabet.indexOf(low) >= 0 ? low : null;
  }
  function starsNode(n, cls) {
    return el("span", { "class": cls, role: "img", "aria-label": t("%lld of 3 stars", n) },
      ["★".repeat(n), el("span", { "class": "off", text: "☆☆☆".slice(0, 3 - n) })]);
  }

  // ---------------------------------------------------------------- days
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function ymd(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  var now = new Date(), TODAY = ymd(now);
  var first = C.firstDay.split("-").map(Number);
  var DAY = Math.max(0, Math.round((Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) - Date.UTC(first[0], first[1] - 1, first[2])) / 864e5));

  // ---------------------------------------------------------------- storage (localStorage only)
  var KEY = "wordmill.web.v1", store;
  try { store = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { store = {}; }
  store.rec = store.rec || {};
  store.days = store.days || [];
  function save() {
    // Keep 60 days of records; the streak only needs the list of days.
    for (var k in store.rec) { var d = +k.split("-")[1]; if (d < DAY - 60) delete store.rec[k]; }
    try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { /* private mode: play on without saving */ }
  }
  function pid(game, level) { return LANG + "-" + DAY + "-" + game + "-" + (level || 0); }
  function rec(id) { return store.rec[id]; }
  function setRec(id, r) {
    store.rec[id] = r;
    if (r.st > 0 && store.days.indexOf(DAY) < 0) store.days.push(DAY);
    save();
  }
  function streak() {
    var set = {}; store.days.forEach(function (d) { set[d] = 1; });
    var d = set[DAY] ? DAY : DAY - 1, n = 0;
    while (set[d]) { n++; d--; }
    return n;
  }
  function bestStreak() {
    var ds = store.days.slice().sort(function (a, b) { return a - b; }), best = 0, run = 0;
    ds.forEach(function (d, i) { run = i && d === ds[i - 1] + 1 ? run + 1 : 1; best = Math.max(best, run); });
    return best;
  }

  // ---------------------------------------------------------------- toast, modal, share
  var toastTimer;
  function toast(msg) {
    var tt = $("toast"); tt.textContent = msg; tt.classList.add("on");
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { tt.classList.remove("on"); }, 1800);
  }
  var lastFocus;
  function openModal(nodes) {
    var sheet = $("sheet"); sheet.innerHTML = "";
    nodes.forEach(function (n) { if (n) sheet.appendChild(n); });
    lastFocus = document.activeElement;
    $("modal").hidden = false;
    var f = sheet.querySelector("button, a"); if (f) f.focus();
  }
  function closeModal() { $("modal").hidden = true; if (lastFocus && lastFocus.focus) lastFocus.focus(); }
  $("modal").addEventListener("click", function (e) { if (e.target === this) closeModal(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !$("modal").hidden) closeModal(); });

  function shareText(text) {
    if (navigator.share && matchMedia("(pointer: coarse)").matches) {
      navigator.share({ text: text }).catch(function () {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () { toast(t("shareCopied")); }, function () { prompt("", text); });
    } else {
      prompt("", text);
    }
  }
  // Model/Share.swift
  function header() { return "Wordmill #" + (DAY + 1) + " · " + LANG.toUpperCase(); }
  function squares(steps, par, hints) {
    var m = [], i;
    for (i = 0; i < Math.min(steps, par); i++) m.push("🟩");
    for (i = 0; i < Math.max(0, steps - par); i++) m.push("🟨");
    for (i = Math.max(0, m.length - hints); i < m.length; i++) m[i] = "💡";
    return m.join("");
  }
  function line(o) {
    var s = "⭐".repeat(o.stars);
    if (o.game === "ladder") return "🪜 " + squares(o.steps, o.par, o.hints) + " " + s;
    if (o.game === "mill") return "🌀 " + t("Mill") + " " + o.found + "/" + o.targets + " " + s + (o.millWord ? " 🌟" : "");
    return "🔐 " + t("Cipher") + " · " + t("Mistakes: %lld", o.mistakes) + " " + s;
  }

  function appBanner() {
    var b = $("appban");
    if (b) { var c = b.cloneNode(true); c.removeAttribute("id"); return c; }
    return el("aside", { "class": "appban" }, [
      el("img", { src: "/wordmill/play/img/icon-128.png", width: 56, height: 56, alt: "", "class": "appicon" }),
      el("div", {}, [el("p", { "class": "apptitle", text: t("getApp") + " " + C.appWords }), el("p", { "class": "apppitch", text: t("appPitch") }),
        el("div", { "class": "badges" }, [
          el("a", { href: C.ios, rel: "noopener", target: EMBED ? "_blank" : null }, [el("img", { src: "/wordmill/play/img/appstore.svg", width: 120, height: 40, alt: t("appStoreAlt") })]),
          el("a", { href: C.play, rel: "noopener", target: EMBED ? "_blank" : null }, [el("img", { src: "/wordmill/play/img/play-" + LANG + ".png", width: 135, height: 40, alt: t("playAlt") })])])])]);
  }

  /** ResultSheet.swift */
  function result(o) {
    var stats = el("div", { "class": "statrow" }, o.stats.map(function (s) {
      return el("div", { "class": "stat" }, [el("b", { text: s[0] }), el("span", { text: t(s[1]) })]);
    }));
    openModal([
      el("p", { "class": "bigstars", style: "text-align:center;margin:0" }, [starsNode(o.stars, "")]),
      el("h2", { id: "mtitle", text: o.headline }),
      el("p", { "class": "sub", text: C.name + " · #" + (DAY + 1) }),
      stats, o.detail,
      el("div", { "class": "sharebox" }, [
        el("button", { "class": "pill", type: "button", text: t("Share result"), onclick: function () { shareText([header(), line(o.outcome), C.url].join("\n")); } }),
        EMBED ? null : el("button", { "class": "pill navy", type: "button", text: t("Daily puzzles"), onclick: function () { closeModal(); location.hash = ""; } })]),
      appBanner(),
      el("button", { "class": "ctl", type: "button", style: "width:100%", text: t("close"), onclick: closeModal })]);
  }

  // ---------------------------------------------------------------- data
  var data = null, dicts = {};
  function decode(s, key) {
    var raw = atob(s), k = new TextEncoder().encode(key), b = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) b[i] = raw.charCodeAt(i) ^ k[i % k.length];
    return JSON.parse(new TextDecoder().decode(b));
  }
  function loadDay() {
    return fetch("/wordmill/play/data/" + LANG + "/" + TODAY + ".json").then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (j) {
      var d = decode(j.d, "wm" + TODAY + LANG);
      if (d.day !== DAY) throw new Error("day");
      return d;
    });
  }
  function loadDict(n) {
    if (!dicts[n]) {
      dicts[n] = fetch("/wordmill/play/dict/" + LANG + "/" + n + ".json").then(function (r) { return r.json(); }).then(function (j) {
        var c = new Set(j.c.split(" ")), v = new Set(j.v.split(" "));
        j.c.split(" ").forEach(function (w) { v.add(w); });
        return { common: c, valid: v };
      });
    }
    return dicts[n];
  }

  // ---------------------------------------------------------------- game shell
  var game = null; // the open game: {key(letter), back(), ...}
  function shell(title, detail, opts) {
    var g = $("game"); g.innerHTML = "";
    var side = el("div", { "class": "gside" });
    var bar = el("div", { "class": "gbar" }, [
      EMBED ? el("div", { "class": "gside" }) : el("button", { "class": "back", type: "button", "aria-label": t("Back"), text: "‹", onclick: function () { location.hash = ""; } }),
      el("div", { "class": "gtitle" }, [el("b", { id: "gtitle", text: title }), el("small", { text: detail })]), side]);
    g.appendChild(bar);
    return { g: g, side: side };
  }
  function keyboard(onKey) {
    var many = C.keyboard.length > 3;
    return el("div", { "class": "kb" + (many ? " many" : ""), role: "group", "aria-label": "Keyboard" }, C.keyboard.map(function (row) {
      return el("div", { "class": "kbrow" }, Array.from(row).map(function (ch) {
        return el("button", { "class": "key", type: "button", text: up(ch), onclick: function () { onKey(ch); } });
      }));
    }));
  }
  function controls(list) {
    return el("div", { "class": "gctl" }, list.map(function (c) {
      return el("button", { "class": "ctl", type: "button", text: c[0], onclick: c[1], id: c[2] || null });
    }));
  }
  function shakeIt(node) { node.classList.remove("shake"); void node.offsetWidth; node.classList.add("shake"); }
  function solvedPanel(st, msg, cls, onResult) {
    return el("div", { "class": "solvedpanel" }, [el("div", { "class": "bigstars" }, [starsNode(st, "")]),
      el("p", { "class": cls || "", text: msg }),
      el("button", { "class": "pill", type: "button", text: t("See result"), onclick: onResult })]);
  }
  document.addEventListener("keydown", function (e) {
    if (!game || !$("modal").hidden || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if (game.onKeyDown && game.onKeyDown(e)) { e.preventDefault(); return; }
    if (e.key.length === 1 || Array.from(e.key).length === 1) {
      var l = gameLetter(e.key);
      if (l && game.key) { e.preventDefault(); game.key(l); }
    }
  });

  // ---------------------------------------------------------------- Ladder (LadderModel.swift)
  function Ladder(level) {
    var p = data.ladders[level], id = pid("ladder", level), r = rec(id) || {};
    var par = p.p.length - 1, path = r.w && r.w.length ? r.w.slice() : [p.s], hints = r.h || 0, solved = !!r.s, sel = null, book = null;
    var sh = shell(t("Ladder"), [t("Easy"), t("Medium"), t("Hard")][level] + " · #" + (DAY + 1));
    var stats = el("div", { "class": "gstats" }), body = el("div", { "class": "gbody" }), bottom = el("div");
    sh.g.appendChild(stats); sh.g.appendChild(body); sh.g.appendChild(bottom);
    var kb = keyboard(function (ch) { type(ch); });
    kb.setAttribute("aria-disabled", "true");
    loadDict(p.s.length).then(function (b) { book = b; kb.removeAttribute("aria-disabled"); });

    function cur() { return path[path.length - 1]; }
    function steps() { return path.length - 1; }
    function starsN() {
      if (!solved) return 0;
      var base = steps() <= par ? 3 : steps() <= par + 2 ? 2 : 1;
      return Math.max(1, base - hints);
    }
    function isWord(w) { return book && book.valid.has(w); }
    function message() {
      if (steps() < par) return t("Record! Shorter than the best path.");
      if (steps() === par) return t("Perfect! You took the shortest path.");
      return t("Solved in %lld steps.", steps());
    }
    function persist() { setRec(id, { w: path, h: hints, s: solved, st: starsN(), g: "ladder" }); }
    function diffIndex(a, b) {
      var A = Array.from(a), B = Array.from(b), d = null;
      for (var i = 0; i < A.length; i++) if (A[i] !== B[i]) { if (d !== null) return null; d = i; }
      return d;
    }
    function render() {
      stats.innerHTML = "";
      stats.appendChild(el("span", { text: "🪜 " + t("%lld steps", steps()) }));
      stats.appendChild(el("span", { text: "🏁 " + t("Best: %lld", par) }));
      body.innerHTML = "";
      var lad = el("div", { "class": "ladder" + (p.s.length === 4 ? " l4" : "") });
      var target = Array.from(p.t);
      path.forEach(function (w, i) {
        var isCur = i === path.length - 1 && !solved, changed = i > 0 ? diffIndex(w, path[i - 1]) : null;
        var solvedRow = solved && i === path.length - 1;
        var row = el("div", { "class": "lrow" + (isCur ? " cur" : "") });
        Array.from(w).forEach(function (c, j) {
          var cls = "tile" + (solvedRow ? " solved" : isCur && sel === j ? " selected" : changed === j ? " changed" : "") +
            (!solvedRow && c === target[j] ? " match" : "") + (!isCur && !solved ? " old" : "");
          row.appendChild(isCur
            ? el("button", { "class": cls, type: "button", text: up(c), "aria-pressed": sel === j ? "true" : "false",
              "aria-label": (j + 1) + ": " + up(c), onclick: function () { sel = sel === j ? null : j; render(); } })
            : el("div", { "class": cls, text: up(c) }));
        });
        lad.appendChild(row);
        if (i < path.length - 1 || !solved) lad.appendChild(el("div", { "class": "rung", "aria-hidden": "true" }));
      });
      if (!solved) {
        lad.appendChild(el("div", { "class": "tlabel", text: t("TARGET") }));
        lad.appendChild(el("div", { "class": "lrow" }, target.map(function (c) { return el("div", { "class": "tile target", text: up(c) }); })));
      }
      body.appendChild(lad);
      body.scrollTop = body.scrollHeight;
      bottom.innerHTML = "";
      if (solved) {
        bottom.appendChild(solvedPanel(starsN(), message(), "", showResult));
      } else {
        bottom.appendChild(controls([[t("Undo"), undo, "undo"], ["💡 " + t("Hint"), hint], [t("Restart"), restart, "restart"]]));
        bottom.querySelector("#undo").disabled = bottom.querySelector("#restart").disabled = path.length < 2;
        bottom.appendChild(kb);
      }
    }
    function reject(msg) { toast(msg); var row = body.querySelector(".lrow.cur"); if (row) shakeIt(row); }
    function type(ch) {
      if (solved) return;
      if (sel === null) { toast(t("Tap the letter you want to change first")); return; }
      var letters = Array.from(cur());
      if (letters[sel] === ch) return;
      letters[sel] = ch;
      var cand = letters.join("");
      if (path.indexOf(cand) >= 0) reject(t("You already used this word"));
      else if (cand === p.t || isWord(cand)) {
        path.push(cand); sel = null;
        if (cand === p.t) solved = true;
        persist(); render();
        if (solved) solvedNow();
      } else reject(t("%@ is not in the word list", up(cand)));
    }
    function undo() { if (!solved && path.length > 1) { path.pop(); sel = null; persist(); render(); } }
    function restart() { if (!solved) { path = [p.s]; sel = null; persist(); render(); } }
    // WordBook.shortestPath: familiar words first, then any valid word.
    function bfs(start, goal, words, used) {
      if (start === goal) return [start];
      var alpha = Array.from(C.alphabet), prev = {}, queue = [start], head = 0;
      prev[start] = start;
      while (head < queue.length) {
        var w = queue[head++], ls = Array.from(w);
        for (var i = 0; i < ls.length; i++) {
          var o = ls[i];
          for (var a = 0; a < alpha.length; a++) {
            var c = alpha[a]; if (c === o) continue;
            ls[i] = c;
            var nx = ls.join("");
            if (prev[nx] === undefined && (nx === goal || (words.has(nx) && !used.has(nx)))) {
              prev[nx] = w;
              if (nx === goal) {
                var out = [nx], x = w;
                while (x !== start) { out.push(x); x = prev[x]; }
                out.push(start);
                return out.reverse();
              }
              queue.push(nx);
            }
          }
          ls[i] = o;
        }
      }
      return null;
    }
    function hint() {
      if (solved || !book) return;
      var used = new Set(path.slice(0, -1));
      var route = bfs(cur(), p.t, book.common, used) || bfs(cur(), p.t, book.valid, used);
      if (!route || route.length < 2) { reject(t("No way to the target from here, step back")); return; }
      hints++; sel = null; path.push(route[1]);
      if (route[1] === p.t) solved = true;
      persist(); render();
      if (solved) solvedNow();
    }
    function solvedNow() { refreshToday(); setTimeout(showResult, 700); }
    function showResult() {
      var detail = el("div", { "class": "detail" }, [el("h3", { text: t("Your ladder") }), el("p", { text: path.map(up).join("  →  ") })]);
      if (path.join() !== p.p.join()) {
        detail.appendChild(el("h3", { text: t("One of the shortest") }));
        detail.appendChild(el("p", { text: p.p.map(up).join("  →  ") }));
      }
      result({ stars: starsN(), headline: message(), detail: detail,
        stats: [[String(steps()), "steps"], [String(par), "best"], [String(hints), "hints"]],
        outcome: { game: "ladder", steps: steps(), par: par, hints: hints, stars: starsN() } });
    }
    render();
    return {
      key: type,
      onKeyDown: function (e) {
        var n = Array.from(cur()).length;
        if (e.key === "Backspace") { undo(); return true; }
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          sel = sel === null ? (e.key === "ArrowRight" ? 0 : n - 1) : (sel + (e.key === "ArrowRight" ? 1 : n - 1)) % n;
          render(); return true;
        }
        if (/^[1-9]$/.test(e.key) && +e.key <= n) { sel = +e.key - 1; render(); return true; }
        return false;
      }
    };
  }
  function ladderOutcome(level) {
    var r = rec(pid("ladder", level));
    if (!r || !r.s) return null;
    var par = data.ladders[level].p.length - 1;
    return { game: "ladder", steps: r.w.length - 1, par: par, hints: r.h, stars: r.st };
  }

  // ---------------------------------------------------------------- Mill (MillModel.swift)
  function Mill() {
    var m = data.mill, id = pid("mill"), r = rec(id) || {};
    var targets = m.t, tset = new Set(m.t), mills = new Set(m.m), words = new Set(m.t.concat(m.b, m.m));
    var letters = Array.from(m.l), found = (r.w || []).slice(), hints = r.h || 0, picked = [];
    var sh = shell(t("Mill"), "#" + (DAY + 1));
    var resultBtn = el("button", { type: "button", "aria-label": t("See result"), text: "🏅", hidden: true, onclick: function () { showResult(); } });
    sh.side.appendChild(resultBtn);
    var prog = el("div", { "class": "mprog" }), body = el("div", { "class": "gbody" }), word = el("div", { "class": "mword", "aria-live": "polite" });
    var wheel = el("div", { "class": "wheel" });
    sh.g.appendChild(prog); sh.g.appendChild(body); sh.g.appendChild(word); sh.g.appendChild(wheel);
    sh.g.appendChild(controls([[t("Delete"), backspace], [t("Shuffle"), shuffle], ["💡 " + t("Hint"), hint]]));
    var enter = el("button", { "class": "pill navy enter", type: "button", text: t("Enter"), onclick: submit });
    sh.g.appendChild(enter);

    function foundTargets() { return found.filter(function (w) { return tset.has(w); }).length; }
    function frac() { return targets.length ? foundTargets() / targets.length : 0; }
    function starsN() { var f = frac(); return f >= 0.9 ? 3 : f >= 0.6 ? 2 : f >= 0.3 ? 1 : 0; }
    function complete() { return foundTargets() === targets.length; }
    function current() { return picked.map(function (i) { return letters[i]; }).join(""); }
    function render() {
      prog.innerHTML = "";
      var bar = el("div", { "class": "bar", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": targets.length, "aria-valuenow": foundTargets() },
        [el("i", { style: "width:" + (frac() * 100) + "%" })]);
      [0.3, 0.6, 0.9].forEach(function (mk) { bar.appendChild(el("b", { "class": frac() >= mk ? "on" : "", style: "left:" + mk * 100 + "%", text: "★" })); });
      prog.appendChild(bar);
      prog.appendChild(el("p", { "class": "mcount", text: t("%lld of %lld words", foundTargets(), targets.length) }));
      body.innerHTML = "";
      if (!found.length) body.appendChild(el("p", { "class": "empty", text: t("Words you find appear here") }));
      else body.appendChild(el("div", { "class": "chips" }, found.map(function (w) {
        return el("span", { "class": "chip" + (mills.has(w) ? " mill" : !tset.has(w) ? " bonus" : ""), text: up(w) });
      })));
      word.textContent = picked.length ? up(current()) : " ";
      wheel.innerHTML = "";
      wheel.appendChild(el("div", { "class": "hub", "aria-hidden": "true" }));
      var n = letters.length;
      letters.forEach(function (c, i) {
        var ang = i / n * 2 * Math.PI - Math.PI / 2, used = picked.indexOf(i) >= 0;
        wheel.appendChild(el("button", { "class": "wl", type: "button", text: up(c), disabled: used, "aria-label": up(c),
          style: "left:" + (132 + Math.cos(ang) * 92) + "px;top:" + (132 + Math.sin(ang) * 92) + "px",
          onclick: function () { tap(i); } }));
      });
      enter.disabled = !picked.length;
      resultBtn.hidden = starsN() === 0;
    }
    function tap(i) { if (picked.indexOf(i) < 0) { picked.push(i); render(); } }
    function backspace() { picked.pop(); render(); }
    function shuffle() {
      picked = [];
      for (var i = letters.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), x = letters[i]; letters[i] = letters[j]; letters[j] = x; }
      render();
    }
    function reject(msg) { toast(msg); shakeIt(word); }
    function submit() {
      var w = current(); picked = [];
      if (Array.from(w).length < 3) { render(); reject(t("Words need at least 3 letters")); return; }
      if (found.indexOf(w) >= 0) { render(); reject(t("Already found")); return; }
      if (!words.has(w)) { render(); reject(t("%@ is not in the word list", up(w))); return; }
      add(w);
      if (mills.has(w)) toast(t("Mill word! Every letter used"));
      else if (!tset.has(w)) toast(t("Bonus word"));
    }
    function hint() {
      var w = targets.slice().reverse().filter(function (x) { return found.indexOf(x) < 0; })[0];
      if (!w) return;
      hints++; add(w);
    }
    function add(w) {
      var before = starsN();
      found.unshift(w);
      setRec(id, { w: found, h: hints, s: starsN() > 0, st: starsN(), g: "mill" });
      render();
      var st = starsN();
      if (st !== before && st > 0) {
        refreshToday();
        if (complete() || st === 1) setTimeout(showResult, 600);
      }
    }
    function showResult() {
      var done = complete();
      result({ stars: starsN(), headline: done ? t("Every word found!") : t("Nice milling!"),
        detail: el("div", { "class": "detail" }, [el("h3", { text: done ? t("All words") : t("Still to find") }),
          el("p", { "class": "muted", style: "font-weight:400", text: done ? t("You found every familiar word in these letters.") : t("Keep going, you can come back to this mill any time today.") })]),
        stats: [[foundTargets() + "/" + targets.length, "words"], [String(found.length - foundTargets()), "bonus"], [String(hints), "hints"]],
        outcome: millOutcome() });
    }
    render();
    return {
      key: function (l) { for (var i = 0; i < letters.length; i++) if (letters[i] === l && picked.indexOf(i) < 0) return tap(i); },
      onKeyDown: function (e) {
        if (e.key === "Backspace") { backspace(); return true; }
        if (e.key === "Enter") { if (picked.length) submit(); return true; }
        if (e.key === " ") { shuffle(); return true; }
        return false;
      }
    };
  }
  function millOutcome() {
    var r = rec(pid("mill"));
    if (!r || !(r.st > 0)) return null;
    var m = data.mill, tset = new Set(m.t);
    return { game: "mill", found: r.w.filter(function (w) { return tset.has(w); }).length, targets: m.t.length,
      millWord: r.w.some(function (w) { return m.m.indexOf(w) >= 0; }), stars: r.st };
  }

  // ---------------------------------------------------------------- Cipher (CipherModel.swift)
  function Cipher() {
    var c = data.cipher, id = pid("cipher"), r = rec(id) || {};
    var numbers = c.n, byNumber = {};
    for (var k in numbers) byNumber[numbers[k]] = k;
    var cells = Array.from(c.p).map(function (ch) { var l = gameLetter(ch); return { o: ch, l: l, n: l ? numbers[l] : null }; });
    var distinct = new Set(cells.filter(function (x) { return x.l; }).map(function (x) { return x.l; }));
    var known = new Set(r.k && r.k.length ? r.k : c.k), mistakes = r.m || 0, hints = r.h || 0, sel = null;
    var title = EMBED ? t("proverbOfDay") : t("Cipher");
    var sh = shell(title, (EMBED ? C.name + " · " : "") + "#" + (DAY + 1));
    var stats = el("div", { "class": "gstats" }), body = el("div", { "class": "gbody" }), bottom = el("div");
    sh.g.appendChild(stats); sh.g.appendChild(body); sh.g.appendChild(bottom);
    var kb = keyboard(function (ch) { type(ch); });
    if (EMBED) sh.g.appendChild(el("p", { "class": "efoot" }, [el("a", { href: C.url, target: "_blank", rel: "noopener", text: t("playMore") + " ↗" })]));

    function solved() { for (var l of distinct) if (!known.has(l)) return false; return true; }
    function starsN() { if (!solved()) return 0; var base = mistakes === 0 ? 3 : mistakes <= 2 ? 2 : 1; return Math.max(1, base - hints); }
    function persist() { setRec(id, { k: Array.from(known), m: mistakes, h: hints, s: solved(), st: starsN(), g: "cipher" }); }
    function nextUnknown() { for (var i = 0; i < cells.length; i++) if (cells[i].l && !known.has(cells[i].l)) return cells[i].n; return null; }
    if (!solved()) sel = nextUnknown();
    function render() {
      stats.innerHTML = "";
      stats.appendChild(el("span", { text: "✖ " + t("Mistakes: %lld", mistakes) }));
      stats.appendChild(el("span", { text: "💡 " + t("Hints: %lld", hints) }));
      body.innerHTML = "";
      var wrap = el("div", { "class": "cwords" }), group = el("div", { "class": "cword" }), done = solved();
      function flush() { if (group.childNodes.length) wrap.appendChild(group); group = el("div", { "class": "cword" }); }
      cells.forEach(function (x) {
        if (x.o === " ") { flush(); return; }
        if (!x.l) { group.appendChild(el("span", { "class": "punct", text: x.o })); return; }
        var kn = known.has(x.l), s = sel === x.n && !kn;
        group.appendChild(el("button", { "class": "cell" + (kn ? " known" : "") + (s ? " sel" : ""), type: "button",
          "aria-label": kn ? up(done ? x.o : x.l) : String(x.n), "aria-pressed": s ? "true" : "false",
          onclick: function () { if (!done && !kn) { sel = sel === x.n ? null : x.n; render(); } } },
          [el("span", { "class": "box", text: kn ? up(done ? x.o : x.l) : " " }), el("span", { "class": "num", text: kn ? " " : String(x.n) })]));
      });
      flush();
      body.appendChild(wrap);
      bottom.innerHTML = "";
      if (done) {
        bottom.appendChild(solvedPanel(starsN(), EMBED ? t("embedSolved") : c.p, EMBED ? "" : "solvedproverb", showResult));
      } else {
        bottom.appendChild(controls([["💡 " + t("Hint"), hint]]));
        bottom.appendChild(kb);
      }
    }
    function type(l) {
      if (solved()) return;
      if (sel === null) { toast(t("Tap a numbered square first")); return; }
      if (l === byNumber[sel]) reveal(l);
      else { mistakes++; toast(t("Not that letter")); persist(); render(); shakeIt(body.querySelector(".cwords")); }
    }
    function hint() {
      if (solved()) return;
      var target = sel !== null ? byNumber[sel] : null;
      if (!target) {
        var counts = {}, best = 0;
        cells.forEach(function (x) { if (x.l && !known.has(x.l)) counts[x.l] = (counts[x.l] || 0) + 1; });
        for (var l in counts) if (counts[l] > best) { best = counts[l]; target = l; }
      }
      if (!target) return;
      hints++; reveal(target);
    }
    function reveal(l) {
      known.add(l); sel = nextUnknown(); persist(); render();
      if (solved()) { refreshToday(); setTimeout(showResult, 700); }
    }
    function showResult() {
      result({ stars: starsN(), headline: mistakes === 0 ? t("Cracked without a mistake!") : t("Code cracked!"),
        detail: el("div", { "class": "detail" }, [el("h3", { text: t("Today's proverb") }), el("p", { "class": "solvedproverb", text: "“" + c.p + "”" })]),
        stats: [[String(mistakes), "mistakes"], [String(hints), "hints"], [String(distinct.size), "letters"]],
        outcome: { game: "cipher", mistakes: mistakes, stars: starsN() } });
    }
    render();
    return {
      key: type,
      onKeyDown: function (e) {
        if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return false;
        var order = [];
        cells.forEach(function (x) { if (x.l && !known.has(x.l) && order.indexOf(x.n) < 0) order.push(x.n); });
        if (!order.length) return true;
        var i = order.indexOf(sel);
        sel = order[(i + (e.key === "ArrowRight" ? 1 : order.length - 1) + (i < 0 ? 1 : 0)) % order.length];
        render(); return true;
      }
    };
  }
  function cipherOutcome() {
    var r = rec(pid("cipher"));
    return r && r.s ? { game: "cipher", mistakes: r.m, stars: r.st } : null;
  }

  // ---------------------------------------------------------------- today screen
  function outcomes() { return [ladderOutcome(0), ladderOutcome(1), ladderOutcome(2), millOutcome(), cipherOutcome()]; }
  function refreshToday() {
    if (EMBED || !data) return;
    var os = outcomes(), keys = ["ladder-0", "ladder-1", "ladder-2", "mill", "cipher"], pts = 0;
    keys.forEach(function (k, i) {
      var r = rec(pid(k.split("-")[0], +(k.split("-")[1] || 0))), st = r ? r.st || 0 : 0, card = $("c-" + k);
      pts += st;
      var s = card.querySelector(".cstars");
      s.innerHTML = ""; s.appendChild(document.createTextNode("★★★".slice(0, st))); s.appendChild(el("span", { "class": "off", text: "☆☆☆".slice(0, 3 - st) }));
      card.classList.toggle("solved", !!(os[i]));
      card.setAttribute("aria-label", card.querySelector("b").textContent + ", " + card.querySelector("small").textContent + ", " + t("%lld of 3 stars", st));
    });
    $("points").textContent = t("Today %lld/%lld", pts, 15);
    $("hstreak").textContent = "🔥 " + streak();
    $("shareDay").hidden = !os.some(Boolean);
  }
  function shareDay() {
    var os = outcomes().filter(Boolean), pts = os.reduce(function (a, o) { return a + o.stars; }, 0);
    shareText([header()].concat(os.map(line), [t("Today %lld/%lld", pts, 15) + " · 🔥 " + streak(), C.url]).join("\n"));
  }
  function statsSheet() {
    var solvedN = 0, starsSum = 0;
    for (var k in store.rec) if (store.rec[k].st > 0) { solvedN++; starsSum += store.rec[k].st; }
    openModal([el("h2", { id: "mtitle", text: t("stats") }),
      el("div", { "class": "statrow" }, [[streak(), "Current streak"], [bestStreak(), "Best streak"]].map(function (s) {
        return el("div", { "class": "stat" }, [el("b", { text: String(s[0]) }), el("span", { text: t(s[1]) })]); })),
      el("div", { "class": "statrow" }, [[store.days.length, "Days played"], [solvedN, "Puzzles solved"], [starsSum, "Stars"]].map(function (s) {
        return el("div", { "class": "stat" }, [el("b", { text: String(s[0]) }), el("span", { text: t(s[1]) })]); })),
      el("p", { "class": "sub", text: t("Every day brings new puzzles in each language. Solve at least one a day to grow your streak.") }),
      appBanner(),
      el("button", { "class": "ctl", type: "button", style: "width:100%", text: t("close"), onclick: closeModal })]);
  }
  function countdown() {
    var n = new Date(), mid = new Date(n.getFullYear(), n.getMonth(), n.getDate() + 1), s = Math.max(0, Math.floor((mid - n) / 1000));
    if (ymd(n) !== TODAY) { location.reload(); return; }
    $("next").textContent = t("New puzzles in %@", pad(Math.floor(s / 3600)) + ":" + pad(Math.floor(s / 60) % 60) + ":" + pad(s % 60));
  }

  // ---------------------------------------------------------------- routing
  function route() {
    var h = location.hash.slice(1);
    if (!data) return;
    var m = /^(ladder)-([0-2])$/.exec(h);
    if (EMBED) { game = Cipher(); return; }
    if (m || h === "mill" || h === "cipher") {
      document.body.classList.add("ingame");
      $("game").hidden = false;
      game = m ? Ladder(+m[2]) : h === "mill" ? Mill() : Cipher();
      var f = $("gtitle"); if (f) { f.setAttribute("tabindex", "-1"); f.focus({ preventScroll: true }); }
      window.scrollTo(0, 0);
    } else {
      var wasGame = document.body.classList.contains("ingame");
      document.body.classList.remove("ingame");
      $("game").hidden = true; $("game").innerHTML = ""; game = null;
      refreshToday();
      if (wasGame) { var card = $("c-" + (lastGame || "")); if (card) card.focus({ preventScroll: false }); }
    }
    lastGame = h || lastGame;
  }
  var lastGame = null;

  function start() {
    if (!EMBED) {
      $("dayline").textContent = "Wordmill #" + (DAY + 1) + " · " + new Intl.DateTimeFormat(LOC, { day: "numeric", month: "long", year: "numeric" }).format(now);
      $("statsBtn").addEventListener("click", statsSheet);
      $("shareDay").addEventListener("click", shareDay);
      $("langSel").addEventListener("change", function () { location.href = "/wordmill/play/" + this.value + "/"; });
      $("hstreak").textContent = "🔥 " + streak();
      countdown(); setInterval(countdown, 1000);
      document.addEventListener("visibilitychange", function () { if (!document.hidden && ymd(new Date()) !== TODAY) location.reload(); });
      if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("/wordmill/play/sw.js").catch(function () {});
    }
    loadDay().then(function (d) {
      data = d;
      window.addEventListener("hashchange", route);
      route();
      if (!EMBED) refreshToday();
    }, function () {
      var msg = el("p", { "class": "empty", text: t("notReady") });
      if (EMBED) $("game").appendChild(msg);
      else $("cards").parentNode.insertBefore(msg, $("cards"));
    });
  }
  start();
})();
