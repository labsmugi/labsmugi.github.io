// Wordmill landing (/wordmill/) and league join page (/wordmill/j/?c=CODE): texts in the app's 15 languages
// and the store links. Plain script, no build step; both pages load it with <script src>.
(function () {
  "use strict";

  var APP_STORE_ID = "6829465408";
  // App Store Connect → Apps → Wordmill → App Analytics → Acquisition → Campaigns → "Generate a Campaign Link"
  // shows the provider token (pt=…). Without it Apple ignores the ct= campaign token.
  var APP_STORE_PROVIDER = "";
  var PACKAGE = "com.mugilabs.wordmill";
  var ALPHABET = /[^ABCDEFGHJKLMNPQRSTUVWXYZ23456789]/g;

  var T = {
    en: { play: "Play in your browser", title: "Wordmill: daily word puzzles", invited: "You're invited to a Wordmill league!",
      lead: "Daily word puzzles in 15 languages: a word ladder, a word wheel and a proverb cipher.",
      joinLead: "Solve the five daily puzzles and compare scores with your friends every week.",
      code: "League code", copy: "Copy code", copied: "Copied!", open: "Already have Wordmill? Open the league",
      steps: "Install Wordmill and open it: you'll go straight to the league. If not, tap Leagues → Join with a code.",
      stepsIos: "Tap Copy code first, then install Wordmill. When you open it, tap Paste to join.",
      noCode: "This invite link is missing its code. Ask your friend to send it again." },
    tr: { play: "Tarayıcıda oyna", title: "Wordmill: günlük kelime bulmacaları", invited: "Bir Wordmill ligine davet edildin!",
      lead: "15 dilde günlük kelime bulmacaları: kelime merdiveni, kelime değirmeni ve atasözü şifresi.",
      joinLead: "Her gün beş bulmacayı çöz, puanlarını her hafta arkadaşlarınla karşılaştır.",
      code: "Lig kodu", copy: "Kodu kopyala", copied: "Kopyalandı!", open: "Wordmill yüklü mü? Ligi aç",
      steps: "Wordmill’i yükleyip aç: doğrudan lige gideceksin. Gitmezsen Ligler → Kodla katıl’a dokun.",
      stepsIos: "Önce Kodu kopyala’ya dokun, sonra Wordmill’i yükle. Açınca katılmak için Yapıştır’a dokun.",
      noCode: "Bu davet bağlantısında kod yok. Arkadaşından tekrar göndermesini iste." },
    de: { play: "Im Browser spielen", title: "Wordmill: tägliche Worträtsel", invited: "Du bist zu einer Wordmill-Liga eingeladen!",
      lead: "Tägliche Worträtsel in 15 Sprachen: Wortleiter, Wortrad und Sprichwort-Code.",
      joinLead: "Löse die fünf Tagesrätsel und vergleiche jede Woche deine Punkte mit Freunden.",
      code: "Liga-Code", copy: "Code kopieren", copied: "Kopiert!", open: "Hast du Wordmill schon? Liga öffnen",
      steps: "Installiere Wordmill und öffne es: Du landest direkt in der Liga. Sonst tippe auf Ligen → Mit Code beitreten.",
      stepsIos: "Tippe zuerst auf Code kopieren und installiere dann Wordmill. Tippe beim Öffnen auf Einsetzen, um beizutreten.",
      noCode: "In diesem Einladungslink fehlt der Code. Bitte deinen Freund, ihn noch einmal zu schicken." },
    fr: { play: "Jouer dans le navigateur", title: "Wordmill : énigmes de mots quotidiennes", invited: "Tu es invité dans une ligue Wordmill !",
      lead: "Des énigmes de mots chaque jour en 15 langues : échelle de mots, roue de lettres et proverbe codé.",
      joinLead: "Résous les cinq énigmes du jour et compare tes points avec tes amis chaque semaine.",
      code: "Code de la ligue", copy: "Copier le code", copied: "Copié !", open: "Tu as déjà Wordmill ? Ouvrir la ligue",
      steps: "Installe Wordmill et ouvre-le : tu arriveras directement dans la ligue. Sinon, touche Ligues → Rejoindre avec un code.",
      stepsIos: "Touche d’abord Copier le code, puis installe Wordmill. À l’ouverture, touche Coller pour rejoindre.",
      noCode: "Il manque le code dans ce lien d’invitation. Demande à ton ami de le renvoyer." },
    es: { play: "Jugar en el navegador", title: "Wordmill: pasatiempos de palabras diarios", invited: "¡Te han invitado a una liga de Wordmill!",
      lead: "Pasatiempos de palabras diarios en 15 idiomas: escalera de palabras, rueda de letras y refrán cifrado.",
      joinLead: "Resuelve los cinco retos del día y compara tus puntos con tus amigos cada semana.",
      code: "Código de la liga", copy: "Copiar código", copied: "¡Copiado!", open: "¿Ya tienes Wordmill? Abrir la liga",
      steps: "Instala Wordmill y ábrelo: irás directo a la liga. Si no, toca Ligas → Unirse con un código.",
      stepsIos: "Toca primero Copiar código y luego instala Wordmill. Al abrirlo, toca Pegar para unirte.",
      noCode: "A este enlace de invitación le falta el código. Pide a tu amigo que lo envíe de nuevo." },
    it: { play: "Gioca nel browser", title: "Wordmill: giochi di parole quotidiani", invited: "Sei stato invitato in una lega di Wordmill!",
      lead: "Giochi di parole ogni giorno in 15 lingue: scala di parole, ruota di lettere e proverbio cifrato.",
      joinLead: "Risolvi i cinque giochi del giorno e confronta i punti con i tuoi amici ogni settimana.",
      code: "Codice della lega", copy: "Copia codice", copied: "Copiato!", open: "Hai già Wordmill? Apri la lega",
      steps: "Installa Wordmill e aprilo: entrerai subito nella lega. Altrimenti tocca Leghe → Entra con un codice.",
      stepsIos: "Tocca prima Copia codice, poi installa Wordmill. Quando lo apri, tocca Incolla per entrare.",
      noCode: "In questo link d’invito manca il codice. Chiedi al tuo amico di rimandarlo." },
    pt: { play: "Jogar no navegador", title: "Wordmill: jogos de palavras diários", invited: "Você foi convidado para uma liga do Wordmill!",
      lead: "Jogos de palavras diários em 15 idiomas: escada de palavras, roda de letras e provérbio cifrado.",
      joinLead: "Resolva os cinco desafios do dia e compare seus pontos com os amigos toda semana.",
      code: "Código da liga", copy: "Copiar código", copied: "Copiado!", open: "Já tem o Wordmill? Abrir a liga",
      steps: "Instale o Wordmill e abra: você vai direto para a liga. Se não for, toque em Ligas → Entrar com um código.",
      stepsIos: "Toque primeiro em Copiar código e depois instale o Wordmill. Ao abrir, toque em Colar para entrar.",
      noCode: "Falta o código neste link de convite. Peça ao seu amigo para enviá-lo de novo." },
    nl: { play: "Speel in je browser", title: "Wordmill: dagelijkse woordpuzzels", invited: "Je bent uitgenodigd voor een Wordmill-competitie!",
      lead: "Dagelijkse woordpuzzels in 15 talen: woordladder, letterrad en spreekwoordcode.",
      joinLead: "Los elke dag de vijf puzzels op en vergelijk elke week je punten met vrienden.",
      code: "Competitiecode", copy: "Code kopiëren", copied: "Gekopieerd!", open: "Heb je Wordmill al? Open de competitie",
      steps: "Installeer Wordmill en open het: je komt meteen in de competitie. Zo niet, tik op Competities → Meedoen met code.",
      stepsIos: "Tik eerst op Code kopiëren en installeer dan Wordmill. Tik bij het openen op Plak om mee te doen.",
      noCode: "Deze uitnodigingslink mist de code. Vraag je vriend om hem opnieuw te sturen." },
    pl: { play: "Graj w przeglądarce", title: "Wordmill: codzienne łamigłówki słowne", invited: "Zaproszono cię do ligi Wordmill!",
      lead: "Codzienne łamigłówki słowne w 15 językach: drabina słów, koło liter i szyfr przysłów.",
      joinLead: "Rozwiązuj pięć codziennych łamigłówek i co tydzień porównuj wyniki ze znajomymi.",
      code: "Kod ligi", copy: "Kopiuj kod", copied: "Skopiowano!", open: "Masz już Wordmill? Otwórz ligę",
      steps: "Zainstaluj Wordmill i otwórz: trafisz prosto do ligi. Jeśli nie, stuknij Ligi → Dołącz z kodem.",
      stepsIos: "Najpierw stuknij Kopiuj kod, potem zainstaluj Wordmill. Po otwarciu stuknij Wklej, aby dołączyć.",
      noCode: "W tym linku z zaproszeniem brakuje kodu. Poproś znajomego, by wysłał go ponownie." },
    sv: { play: "Spela i webbläsaren", title: "Wordmill: dagliga ordpussel", invited: "Du är inbjuden till en Wordmill-liga!",
      lead: "Dagliga ordpussel på 15 språk: ordstege, bokstavshjul och ordspråkskod.",
      joinLead: "Lös dagens fem pussel och jämför poängen med dina vänner varje vecka.",
      code: "Ligakod", copy: "Kopiera kod", copied: "Kopierat!", open: "Har du redan Wordmill? Öppna ligan",
      steps: "Installera Wordmill och öppna appen: du kommer direkt till ligan. Annars trycker du på Ligor → Gå med med kod.",
      stepsIos: "Tryck först på Kopiera kod och installera sedan Wordmill. Tryck på Klistra in när du öppnar appen.",
      noCode: "Den här inbjudningslänken saknar kod. Be din vän att skicka den igen." },
    da: { play: "Spil i browseren", title: "Wordmill: daglige ordgåder", invited: "Du er inviteret til en Wordmill-liga!",
      lead: "Daglige ordgåder på 15 sprog: ordstige, bogstavhjul og ordsprogskode.",
      joinLead: "Løs dagens fem opgaver, og sammenlign point med dine venner hver uge.",
      code: "Ligakode", copy: "Kopiér kode", copied: "Kopieret!", open: "Har du allerede Wordmill? Åbn ligaen",
      steps: "Installer Wordmill, og åbn appen: du kommer direkte ind i ligaen. Ellers tryk på Ligaer → Deltag med kode.",
      stepsIos: "Tryk først på Kopiér kode, og installer så Wordmill. Tryk på Indsæt, når du åbner appen.",
      noCode: "Dette invitationslink mangler koden. Bed din ven om at sende det igen." },
    no: { play: "Spill i nettleseren", title: "Wordmill: daglige ordgåter", invited: "Du er invitert til en Wordmill-liga!",
      lead: "Daglige ordgåter på 15 språk: ordstige, bokstavhjul og ordtakskode.",
      joinLead: "Løs dagens fem oppgaver, og sammenlign poengene med vennene dine hver uke.",
      code: "Ligakode", copy: "Kopier kode", copied: "Kopiert!", open: "Har du allerede Wordmill? Åpne ligaen",
      steps: "Installer Wordmill og åpne appen: du kommer rett inn i ligaen. Hvis ikke, trykk på Ligaer → Bli med med kode.",
      stepsIos: "Trykk først på Kopier kode, og installer så Wordmill. Trykk på Lim inn når du åpner appen.",
      noCode: "Denne invitasjonslenken mangler koden. Be vennen din sende den på nytt." },
    cs: { play: "Hrát v prohlížeči", title: "Wordmill: denní slovní hádanky", invited: "Máš pozvánku do ligy Wordmill!",
      lead: "Denní slovní hádanky v 15 jazycích: slovní žebřík, kolo písmen a šifra přísloví.",
      joinLead: "Vyřeš pět denních hádanek a každý týden porovnávej body s přáteli.",
      code: "Kód ligy", copy: "Kopírovat kód", copied: "Zkopírováno!", open: "Už máš Wordmill? Otevřít ligu",
      steps: "Nainstaluj Wordmill a otevři ho: dostaneš se rovnou do ligy. Když ne, klepni na Ligy → Připojit se kódem.",
      stepsIos: "Nejdřív klepni na Kopírovat kód a pak nainstaluj Wordmill. Po otevření klepni na Vložit.",
      noCode: "V tomhle odkazu s pozvánkou chybí kód. Popros kamaráda, ať ho pošle znovu." },
    ro: { play: "Joacă în browser", title: "Wordmill: jocuri de cuvinte zilnice", invited: "Ai fost invitat într-o ligă Wordmill!",
      lead: "Jocuri de cuvinte zilnice în 15 limbi: scara cuvintelor, roata literelor și proverbul cifrat.",
      joinLead: "Rezolvă cele cinci jocuri ale zilei și compară punctele cu prietenii în fiecare săptămână.",
      code: "Codul ligii", copy: "Copiază codul", copied: "Copiat!", open: "Ai deja Wordmill? Deschide liga",
      steps: "Instalează Wordmill și deschide-l: ajungi direct în ligă. Dacă nu, atinge Ligi → Intră cu un cod.",
      stepsIos: "Atinge întâi Copiază codul, apoi instalează Wordmill. Când îl deschizi, atinge Lipește ca să intri.",
      noCode: "Acestui link de invitație îi lipsește codul. Roagă-ți prietenul să-l trimită din nou." },
    id: { play: "Main di browser", title: "Wordmill: teka-teki kata harian", invited: "Kamu diundang ke liga Wordmill!",
      lead: "Teka-teki kata harian dalam 15 bahasa: tangga kata, roda huruf, dan sandi peribahasa.",
      joinLead: "Selesaikan lima teka-teki harian dan bandingkan skormu dengan teman setiap minggu.",
      code: "Kode liga", copy: "Salin kode", copied: "Tersalin!", open: "Sudah punya Wordmill? Buka liganya",
      steps: "Pasang Wordmill lalu buka: kamu langsung masuk ke liga. Kalau tidak, ketuk Liga → Gabung dengan kode.",
      stepsIos: "Ketuk Salin kode dulu, lalu pasang Wordmill. Saat membukanya, ketuk Tempel untuk bergabung.",
      noCode: "Tautan undangan ini tidak berisi kode. Minta temanmu mengirimkannya lagi." }
  };
  // Google Play badge files per language (Apple's badge is the English one, img/app-store.svg).
  var PLAY_BADGE = { en: "en", tr: "tr", de: "de", fr: "fr", es: "es", it: "it", pt: "pt-br", nl: "nl", pl: "pl",
    sv: "sv", da: "da", no: "no", cs: "cs", ro: "ro", id: "id" };

  function pick(code) {
    code = (code || "").toLowerCase();
    if (code === "nb" || code === "nn") code = "no";
    if (code === "in") code = "id";
    return T[code] ? code : null;
  }

  /** ?l= (the sharer's puzzle language) first, then the browser's languages, then English. */
  function language(params) {
    var fromLink = pick(params.get("l"));
    if (fromLink) return fromLink;
    var list = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "en"];
    for (var i = 0; i < list.length; i++) {
      var lang = pick(String(list[i]).split("-")[0]);
      if (lang) return lang;
    }
    return "en";
  }

  var ua = navigator.userAgent || "";
  var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  var android = /Android/.test(ua);

  function appStore(campaign) {
    return "https://apps.apple.com/app/apple-store/id" + APP_STORE_ID + "?" +
      (APP_STORE_PROVIDER ? "pt=" + APP_STORE_PROVIDER + "&" : "") + "ct=" + encodeURIComponent(campaign) + "&mt=8";
  }

  /** Play hands `referrer` back to the app on first launch (Install Referrer API, core/InstallReferrer.kt). */
  function googlePlay(referrer) {
    return "https://play.google.com/store/apps/details?id=" + PACKAGE + "&referrer=" + encodeURIComponent(referrer);
  }

  /** `base` leads from the page to /wordmill/ ("" or "../"). */
  function badges(el, lang, apple, play, base) {
    var g = PLAY_BADGE[lang];
    el.innerHTML =
      '<a class="badge apple" id="appstore" href="' + apple + '"><img alt="Download on the App Store" src="' + base + 'img/app-store.svg"></a>' +
      '<a class="badge play" id="play" href="' + play + '"><img alt="Get it on Google Play" src="https://play.google.com/intl/en_us/badges/static/images/badges/' + g + '_badge_web_generic.png"' +
      ' onerror="this.onerror=null;this.src=\'https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png\'"></a>';
    // Phones see their own store first; computers see both.
    if (android) el.insertBefore(el.lastChild, el.firstChild);
    if (ios || android) el.children[1].classList.add("other");
  }

  function texts(lang) {
    var t = T[lang];
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-t]").forEach(function (el) { el.textContent = t[el.getAttribute("data-t")]; });
    return t;
  }

  function copy(text, done) {
    function fallback() {
      var area = document.createElement("textarea");
      area.value = text; area.setAttribute("readonly", ""); area.style.position = "fixed"; area.style.opacity = "0";
      document.body.appendChild(area); area.select();
      try { document.execCommand("copy"); } catch (e) { /* nothing more to try */ }
      document.body.removeChild(area);
      if (done) done();
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
    else fallback();
  }

  window.Wordmill = {
    /** The join page: /wordmill/j/?c=CODE (also reached from /wordmill/j/CODE through the site's 404.html). */
    join: function () {
      var params = new URLSearchParams(location.search);
      var lang = language(params);
      var t = texts(lang);
      document.title = t.invited + " · Wordmill";
      var code = (params.get("c") || params.get("join") || "").toUpperCase().replace(ALPHABET, "").slice(0, 6);
      if (code.length !== 6) {
        document.getElementById("invite").hidden = true;
        document.getElementById("nocode").hidden = false;
        badges(document.getElementById("stores"), lang, appStore("league"), googlePlay("utm_source=join"), "../");
        return;
      }
      var link = "https://labsmugi.github.io/wordmill/j/?c=" + code;
      document.getElementById("code").textContent = code;
      document.getElementById("steps").textContent = ios ? t.stepsIos : t.steps;
      var button = document.getElementById("copy");
      // The whole link, not just the code: on iPhone the app offers to paste it on its first launch.
      button.addEventListener("click", function () {
        copy(link, function () { button.textContent = t.copied; button.classList.add("done"); });
      });
      badges(document.getElementById("stores"), lang, appStore("league"), googlePlay("league=" + code), "../");
      // Going to the App Store from here also copies the link, so the paste offer finds it after installing.
      document.getElementById("appstore").addEventListener("click", function () { copy(link); });
      var open = document.getElementById("open");
      var scheme = "wordmill://join/" + code;
      if (android) {
        // Chrome opens the app when installed; otherwise it comes back here (noapp=1, so it isn't tried twice).
        var back = location.href + (location.search ? "&" : "?") + "noapp=1";
        scheme = "intent://join/" + code + "#Intent;scheme=wordmill;package=" + PACKAGE +
          ";S.browser_fallback_url=" + encodeURIComponent(back) + ";end";
        if (!params.get("noapp")) location.replace(scheme);
      }
      // iPhone: Universal Links already open the app before this page loads. Trying wordmill:// unasked
      // would show Safari's "address is invalid" alert to everyone without the app, so it's a link here.
      open.href = scheme;
    },

    /** The landing page: /wordmill/ (?l=xx from shares). Phones go to their store; 1.1 beta invitations to the join page. */
    landing: function () {
      var params = new URLSearchParams(location.search);
      var code = (params.get("join") || params.get("c") || "").toUpperCase().replace(ALPHABET, "").slice(0, 6);
      if (code.length === 6) { location.replace("j/?c=" + code); return; }
      var lang = language(params);
      texts(lang);
      var campaign = "share" + (pick(params.get("l")) ? "-" + pick(params.get("l")) : "");
      var apple = appStore(campaign), play = googlePlay("utm_source=share&utm_campaign=" + campaign);
      badges(document.getElementById("stores"), lang, apple, play, "");
      if (ios) location.replace(apple);
      else if (android) location.replace(play);
    }
  };
})();
