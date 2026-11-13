"""Ezan Vakti web pages outside Turkey: one folder per language under ezan/ (ezan/id/, ezan/ms/ ...).

Each locale below has its places file, its source of times and its texts. Pages per place:
    ezan/<lang>/<place>/                   this month's times, qibla, other places of the region
    ezan/<lang>/<place>/<ramadan slug>/    Ramadan 2027 timetable
    ezan/<lang>/ and ezan/<lang>/<ramadan slug>/   lists of all places
Called from build.py; standard library only.
"""
import calendar
import html
import json
import math
import os
from datetime import date, timedelta

from prayertimes import hhmm, times

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://labsmugi.github.io"
APP_ID = "6825951256"
PKG = "com.mugilabs.ezan"
RAMADAN_START = date(2027, 2, 8)
# Footer of every Ezan page (Turkish ones too): lets visitors and crawlers reach the other languages.
LANG_LINKS = ('<p class="langs"><a href="/ezan/" lang="tr">Türkçe</a> · <a href="/ezan/id/" lang="id">Bahasa Indonesia</a> · '
              '<a href="/ezan/ms/" lang="ms">Bahasa Melayu</a> · <a href="/ezan/ar/" lang="ar">العربية</a> · '
              '<a href="/ezan/bn/" lang="bn">বাংলা</a> · <a href="/ezan/en/" lang="en">English</a></p>')


def e(s):
    return html.escape(str(s), quote=True)


def qibla(lat, lon):
    k_lat, k_lon = math.radians(21.4225), math.radians(39.8262)
    la, lo = math.radians(lat), math.radians(lon)
    d_lon = k_lon - lo
    y = math.sin(d_lon) * math.cos(k_lat)
    x = math.cos(la) * math.sin(k_lat) - math.sin(la) * math.cos(k_lat) * math.cos(d_lon)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    h = math.sin((k_lat - la) / 2) ** 2 + math.cos(la) * math.cos(k_lat) * math.sin(d_lon / 2) ** 2
    return bearing, 6371 * 2 * math.asin(math.sqrt(h))


# ------------------------------------------------------------------ sources of times

class Kemenag:
    """Indonesia: computed with the Kemenag-tuned method (see prayertimes.TUNING)."""
    keys = ("imsak", "subuh", "gunes", "ogle", "ikindi", "aksam", "yatsi")

    def day(self, p, d, ramadan=False):
        t = times(d, p["lat"], p["lon"], p["tz"], "kemenag", elevation=p.get("elev", 0))
        return [hhmm(t[k]) for k in self.keys], False

    def ramadan(self, p):
        # 1 Ramadhan 1448 = 8 Feb 2027 (hisab); 30 rows, the 30th only if the month has 30 days.
        return [(RAMADAN_START + timedelta(days=i), str(i + 1)) for i in range(30)]


class Jakim:
    """Malaysia: JAKIM's published timetable per zone (data/jakim-<year>.json, see fetch_jakim.py).
    A zone JAKIM hasn't published yet for a year uses the same day of the year before (marked)."""

    def __init__(self):
        self.years = {}

    def _year(self, y):
        if y not in self.years:
            path = os.path.join(HERE, "data", f"jakim-{y}.json")
            self.years[y] = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        return self.years[y]

    def row(self, zone, d):
        r = self._year(d.year).get(zone, {}).get(d.isoformat())
        if r:
            return r, False
        try:
            prev = d.replace(year=d.year - 1)
        except ValueError:  # 29 Feb
            prev = d.replace(year=d.year - 1, day=28)
        r = self._year(prev.year).get(zone, {}).get(prev.isoformat())
        if not r:
            return None, True
        hijri = self.hijri(d) or r[0]
        return [hijri] + r[1:], True

    def hijri(self, d):
        for zone_rows in self._year(d.year).values():
            if d.isoformat() in zone_rows:
                return zone_rows[d.isoformat()][0]
        return None

    def day(self, p, d, ramadan=False):
        r, est = self.row(p["zone"], d)
        return (r[1:] if r else ["--:--"] * 7), est

    def ramadan(self, p):
        rows, d = [], RAMADAN_START - timedelta(days=3)
        while d < RAMADAN_START + timedelta(days=35):
            h = self.hijri(d)
            if h and h[5:7] == "09":
                rows.append((d, str(int(h[8:10]))))
            elif h and h[5:10] == "10-01":
                rows.append((d, "–"))
                break
            d += timedelta(days=1)
        return rows


class Computed:
    """Everywhere else: the app's default method for the place's country (prepare_world.py), with the
    pages' safety rules (high-latitude Fajr/Isha, prayer times rounded up; see prayertimes.times)."""
    keys = ("imsak", "gunes", "ogle", "ikindi", "aksam", "yatsi")

    def day(self, p, d, ramadan=False):
        t = times(d, p["lat"], p["lon"], p["tz"], p["method"], hanafi_asr=p.get("hanafi", False),
                  safe=True, ramadan=ramadan)
        return [hhmm(t[k]) for k in self.keys], False

    def ramadan(self, p):
        return [(RAMADAN_START + timedelta(days=i), str(i + 1)) for i in range(30)]


# ------------------------------------------------------------------ locales

LOCALES = {
    "id": {
        "places": "places-id.json", "source": Kemenag, "lang": "id", "locale": "id-ID", "og": "id_ID",
        "store": "id", "app_name": "Waktu Azan", "group_word": "provinsi",
        "cols": ["Imsak", "Subuh", "Terbit", "Dzuhur", "Ashar", "Maghrib", "Isya"], "sun": 2, "iftar": 5,
        "months": "Januari Februari Maret April Mei Juni Juli Agustus September Oktober November Desember".split(),
        "days": "Senin Selasa Rabu Kamis Jumat Sabtu Minggu".split(),
        "days_short": "Sen Sel Rab Kam Jum Sab Min".split(),
        "compass": ["utara", "timur laut", "timur", "tenggara", "selatan", "barat daya", "barat", "barat laut"],
        "next": "{n} dalam {d}", "h": "jam", "m": "menit",
        "root": "Jadwal Sholat",
        "title": "Jadwal Sholat {name} Hari Ini – {month} | Waktu Azan",
        "desc": "Jadwal sholat {name} hari ini: imsak, subuh, dzuhur, ashar, maghrib dan isya. Jadwal sholat bulan {month}, arah kiblat dan jadwal imsakiyah Ramadhan 2027.",
        "h1": "Jadwal Sholat {name}",
        "lead": "Waktu sholat untuk {full}. Jadwal hari ini dan hitung mundur ke waktu sholat berikutnya ada di bawah; jadwal sebulan penuh ada di tabel.",
        "month_h": "Jadwal sholat {name} {month}",
        "date_col": "Tanggal",
        "qibla_h": "Arah kiblat {name}",
        "qibla": "Arah kiblat dari {full}: <b>{deg}°</b> dari utara searah jarum jam (arah {compass}). Jarak ke Ka'bah sekitar <b>{km} km</b>.",
        "others": "Kota lain di {group}",
        "ram_slug": "imsakiyah-ramadhan-2027",
        "ram_btn": "Jadwal Imsakiyah Ramadhan 2027 {name} →",
        "ram_title": "Jadwal Imsakiyah Ramadhan 2027 {name} – Waktu Sahur dan Buka Puasa",
        "ram_desc": "Jadwal imsakiyah Ramadhan 1448 H / 2027 untuk {full}: waktu imsak (akhir sahur) dan maghrib (buka puasa) setiap hari mulai 8 Februari 2027. Hari pertama: imsak {imsak}, buka puasa {iftar}.",
        "ram_h1": "Jadwal Imsakiyah Ramadhan 1448 H / 2027 {name}",
        "ram_lead": "Waktu imsak (akhir sahur) dan maghrib (buka puasa) di {full} selama Ramadhan 1448 H. Jadwal ini memakai perkiraan 1 Ramadhan = Senin, 8 Februari 2027; awal Ramadhan dan Idul Fitri resmi ditetapkan pemerintah melalui sidang isbat.",
        "ram_crumb": "Imsakiyah 2027",
        "ram_day": "Hari", "ram_imsak_sub": "akhir sahur", "ram_iftar_sub": "buka puasa",
        "fact_imsak": "Imsak hari pertama", "fact_iftar": "Buka puasa hari pertama", "fact_last": "Buka puasa terakhir ({d})",
        "note_first": "Puasa pertama", "note_30": "Jika Ramadhan 30 hari", "note_eid": "Idul Fitri",
        "ram_howto_h": "Cara membaca jadwal imsakiyah",
        "ram_howto": "<b>Imsak</b> adalah tanda berhenti makan sahur, 10 menit sebelum <b>Subuh</b> saat puasa dimulai. <b>Maghrib</b> adalah waktu berbuka puasa. Shalat tarawih dilaksanakan setelah shalat Isya.",
        "back": "Jadwal sholat harian {name} →",
        "index_title": "Jadwal Sholat Hari Ini – Seluruh Kota di Indonesia | Waktu Azan",
        "index_desc": "Jadwal sholat hari ini untuk kota-kota di seluruh Indonesia: imsak, subuh, dzuhur, ashar, maghrib, isya, arah kiblat dan jadwal imsakiyah Ramadhan 2027.",
        "index_h1": "Jadwal Sholat Indonesia",
        "index_lead": "Jadwal sholat untuk {n} kota di {g} provinsi Indonesia: waktu sholat hari ini, jadwal sebulan, arah kiblat dan jadwal imsakiyah Ramadhan 2027. Pilih kota Anda.",
        "ram_index_title": "Jadwal Imsakiyah Ramadhan 2027 – Seluruh Kota di Indonesia",
        "ram_index_desc": "Jadwal imsakiyah Ramadhan 1448 H / 2027 untuk kota-kota di seluruh Indonesia: waktu imsak dan buka puasa setiap hari.",
        "ram_index_h1": "Jadwal Imsakiyah Ramadhan 2027",
        "ram_index_lead": "Ramadhan 1448 H diperkirakan dimulai Senin, 8 Februari 2027 (menunggu sidang isbat). Pilih kota Anda untuk melihat waktu imsak dan buka puasa.",
        "app_h": "Dapatkan notifikasi waktu sholat",
        "app_p": "Aplikasi Waktu Azan menghitung jadwal sholat di lokasi Anda tanpa internet dan mengingatkan dengan suara azan; juga ada kompas kiblat, Al-Qur'an, jadwal imsakiyah dan pengingat sahur. Gratis dan tanpa iklan.",
        "method": "Jadwal dihitung dengan kriteria Kementerian Agama RI (Subuh 20°, Isya 18°, ihtiyat dan ketinggian kota). Dibandingkan dengan jadwal resmi Kemenag, sebagian besar waktu sama persis dan sisanya berbeda paling banyak 1 menit.",
        "all": "Semua kota", "privacy": "Privasi", "geo": "Data lokasi",
        "estimate": "",
    },
    "ms": {
        "places": "places-my.json", "source": Jakim, "lang": "ms", "locale": "ms-MY", "og": "ms_MY",
        "store": "my", "app_name": "Waktu Azan", "group_word": "negeri",
        "cols": ["Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"], "sun": 2, "iftar": 5,
        "months": "Januari Februari Mac April Mei Jun Julai Ogos September Oktober November Disember".split(),
        "days": "Isnin Selasa Rabu Khamis Jumaat Sabtu Ahad".split(),
        "days_short": "Isn Sel Rab Kha Jum Sab Ahd".split(),
        "compass": ["utara", "timur laut", "timur", "tenggara", "selatan", "barat daya", "barat", "barat laut"],
        "next": "{n} dalam {d}", "h": "jam", "m": "minit",
        "root": "Waktu Solat",
        "title": "Waktu Solat {name} Hari Ini – {month} | Waktu Azan",
        "desc": "Waktu solat {name} hari ini mengikut JAKIM (zon {zone}): imsak, subuh, zohor, asar, maghrib dan isyak. Jadual waktu solat {month}, arah kiblat dan jadual imsak Ramadan 2027.",
        "h1": "Waktu Solat {name}",
        "lead": "Waktu solat bagi {full} (zon JAKIM {zone}). Waktu hari ini dan kiraan ke solat seterusnya di bawah; jadual sebulan di dalam jadual.",
        "month_h": "Waktu solat {name} {month}",
        "date_col": "Tarikh",
        "qibla_h": "Arah kiblat {name}",
        "qibla": "Arah kiblat dari {full}: <b>{deg}°</b> dari utara mengikut arah jam (arah {compass}). Jarak ke Kaabah kira-kira <b>{km} km</b>.",
        "others": "Kawasan lain di {group}",
        "ram_slug": "jadual-imsak-ramadan-2027",
        "ram_btn": "Jadual Imsak Ramadan 2027 {name} →",
        "ram_title": "Jadual Imsak dan Berbuka Puasa {name} Ramadan 2027",
        "ram_desc": "Jadual waktu imsak dan berbuka puasa {full} bagi Ramadan 1448H / 2027 mengikut JAKIM. Hari pertama: imsak {imsak}, berbuka {iftar}.",
        "ram_h1": "Jadual Imsak & Berbuka Puasa {name} – Ramadan 2027",
        "ram_lead": "Waktu imsak (akhir sahur) dan maghrib (berbuka puasa) di {full} sepanjang Ramadan 1448H mengikut takwim JAKIM, yang meletakkan 1 Ramadan pada Isnin, 8 Februari 2027. Tarikh sebenar awal Ramadan dan Hari Raya Aidilfitri diumumkan oleh Penyimpan Mohor Besar Raja-Raja.",
        "ram_crumb": "Jadual imsak 2027",
        "ram_day": "Hari", "ram_imsak_sub": "akhir sahur", "ram_iftar_sub": "berbuka",
        "fact_imsak": "Imsak hari pertama", "fact_iftar": "Berbuka hari pertama", "fact_last": "Berbuka terakhir ({d})",
        "note_first": "Puasa pertama", "note_30": "", "note_eid": "Hari Raya Aidilfitri",
        "ram_howto_h": "Cara membaca jadual imsak",
        "ram_howto": "<b>Imsak</b> ialah 10 minit sebelum <b>Subuh</b>, tanda berhenti bersahur. <b>Maghrib</b> ialah waktu berbuka puasa. Solat tarawih ditunaikan selepas solat Isyak.",
        "back": "Waktu solat harian {name} →",
        "index_title": "Waktu Solat Malaysia Hari Ini – Semua Zon JAKIM | Waktu Azan",
        "index_desc": "Waktu solat hari ini mengikut JAKIM untuk semua negeri dan kawasan di Malaysia: imsak, subuh, zohor, asar, maghrib, isyak, arah kiblat dan jadual imsak Ramadan 2027.",
        "index_h1": "Waktu Solat Malaysia",
        "index_lead": "Waktu solat rasmi JAKIM untuk {n} kawasan dalam {g} negeri: waktu hari ini, jadual sebulan, arah kiblat dan jadual imsak Ramadan 2027. Pilih kawasan anda.",
        "ram_index_title": "Jadual Imsak dan Berbuka Puasa Ramadan 2027 – Seluruh Malaysia",
        "ram_index_desc": "Jadual imsak dan berbuka puasa Ramadan 1448H / 2027 mengikut JAKIM untuk semua kawasan di Malaysia.",
        "ram_index_h1": "Jadual Imsak Ramadan 2027",
        "ram_index_lead": "Mengikut takwim JAKIM, 1 Ramadan 1448H jatuh pada Isnin, 8 Februari 2027. Pilih kawasan anda untuk melihat waktu imsak dan berbuka.",
        "app_h": "Dapatkan peringatan waktu solat",
        "app_p": "Aplikasi Waktu Azan mengira waktu solat di lokasi anda tanpa internet dan mengingatkan dengan suara azan; juga ada kompas kiblat, Al-Quran, jadual imsak dan peringatan sahur. Percuma dan tanpa iklan.",
        "method": "Waktu solat ialah data rasmi JAKIM (e-solat.gov.my) mengikut zon.",
        "all": "Semua kawasan", "privacy": "Privasi", "geo": "Data lokasi",
        "estimate": "Anggaran: JAKIM belum menerbitkan takwim tahun ini bagi zon ini; waktu diambil daripada tarikh yang sama tahun lepas.",
    },
    "ar": {
        "places": "places-ar.json", "source": Computed, "lang": "ar", "locale": "ar", "og": "ar_AR", "rtl": True,
        "full": "{name}، {group}",
        "store": "", "app_name": "وقت الأذان", "full_month": True,
        "cols": ["الفجر", "الشروق", "الظهر", "العصر", "المغرب", "العشاء"], "sun": 1, "iftar": 4,
        "months": "يناير فبراير مارس أبريل مايو يونيو يوليو أغسطس سبتمبر أكتوبر نوفمبر ديسمبر".split(),
        "days": "الاثنين الثلاثاء الأربعاء الخميس الجمعة السبت الأحد".split(),
        "days_short": "الاثنين الثلاثاء الأربعاء الخميس الجمعة السبت الأحد".split(),
        "compass": ["الشمال", "الشمال الشرقي", "الشرق", "الجنوب الشرقي", "الجنوب", "الجنوب الغربي", "الغرب", "الشمال الغربي"],
        "next": "{n} بعد {d}", "h": "ساعة", "m": "دقيقة",
        "root": "مواقيت الصلاة",
        "title": "مواقيت الصلاة في {name} اليوم – {month} | وقت الأذان",
        "desc": "مواقيت الصلاة في {name} اليوم: الفجر والشروق والظهر والعصر والمغرب والعشاء. جدول مواقيت شهر {month} واتجاه القبلة وإمساكية رمضان 2027.",
        "h1": "مواقيت الصلاة في {name}",
        "lead": "مواعيد الأذان في {full}. مواقيت اليوم والوقت المتبقي للصلاة القادمة في الأعلى، وجدول الشهر كاملاً في الأسفل.",
        "month_h": "مواقيت الصلاة في {name} لشهر {month}",
        "date_col": "التاريخ",
        "qibla_h": "اتجاه القبلة في {name}",
        "qibla": "اتجاه القبلة من {full}: <b>{deg}°</b> من الشمال باتجاه عقارب الساعة (نحو {compass}). المسافة إلى الكعبة نحو <b>{km} كم</b>.",
        "others": "مدن أخرى في {group}",
        "ram_slug": "imsakiya-ramadan-2027",
        "ram_btn": "إمساكية رمضان 2027 في {name} ←",
        "ram_title": "إمساكية رمضان 2027 {name} – مواعيد السحور والإفطار",
        "ram_desc": "إمساكية رمضان 1448 هـ / 2027 في {full}: موعد الإمساك (الفجر) والإفطار (المغرب) يوماً بيوم بدءاً من 8 فبراير 2027. اليوم الأول: الفجر {imsak} والإفطار {iftar}.",
        "ram_h1": "إمساكية رمضان 1448 هـ / 2027 في {name}",
        "ram_lead": "مواعيد الإمساك والإفطار في {full} خلال رمضان 1448 هـ. يبدأ رمضان فلكياً يوم الاثنين 8 فبراير 2027 (تقويم أم القرى)، وقد يتأخر يوماً في بعض الدول بحسب رؤية الهلال.",
        "ram_crumb": "إمساكية 2027",
        "ram_day": "اليوم", "ram_imsak_sub": "الإمساك", "ram_iftar_sub": "الإفطار",
        "fact_imsak": "الإمساك في اليوم الأول", "fact_iftar": "الإفطار في اليوم الأول", "fact_last": "آخر إفطار ({d})",
        "note_first": "أول أيام الصيام", "note_30": "إذا كان الشهر 30 يوماً", "note_eid": "عيد الفطر",
        "ram_howto_h": "كيف تقرأ الإمساكية؟",
        "ram_howto": "يبدأ الصيام مع أذان <b>الفجر</b>، ويُستحب الانتهاء من السحور قبله بدقائق. وقت الإفطار هو أذان <b>المغرب</b>. وتُصلّى التراويح بعد صلاة العشاء.",
        "back": "مواقيت الصلاة اليومية في {name} ←",
        "index_title": "مواقيت الصلاة اليوم في المدن العربية | وقت الأذان",
        "index_desc": "مواقيت الصلاة اليوم في مدن السعودية ومصر والإمارات والعراق والمغرب والجزائر وسائر الدول العربية، مع جدول الشهر واتجاه القبلة وإمساكية رمضان 2027.",
        "index_h1": "مواقيت الصلاة",
        "index_lead": "مواقيت الصلاة في {n} مدينة في {g} دولة عربية: مواقيت اليوم وجدول الشهر واتجاه القبلة وإمساكية رمضان 2027. اختر مدينتك.",
        "ram_index_title": "إمساكية رمضان 2027 – مواعيد السحور والإفطار في المدن العربية",
        "ram_index_desc": "إمساكية رمضان 1448 هـ / 2027 لمدن السعودية ومصر والإمارات والعراق والمغرب وسائر الدول العربية: مواعيد الإمساك والإفطار يوماً بيوم.",
        "ram_index_h1": "إمساكية رمضان 2027",
        "ram_index_lead": "يبدأ شهر رمضان 1448 هـ فلكياً يوم الاثنين 8 فبراير 2027، ويُعلن بدايته رسمياً في كل دولة. اختر مدينتك لمعرفة مواعيد الإمساك والإفطار.",
        "app_h": "احصل على تنبيه الأذان",
        "app_p": "تطبيق وقت الأذان يحسب مواقيت الصلاة في موقعك دون إنترنت وينبّهك بصوت الأذان، ومعه بوصلة القبلة والقرآن الكريم والإمساكية وتذكير السحور. مجاني وبلا إعلانات.",
        "method": "تُحسب المواقيت بالطريقة المعتمدة في كل دولة كما في التطبيق: أم القرى في السعودية ودول الخليج، والهيئة المصرية العامة للمساحة في مصر والسودان والشام والعراق، وطريقة دبي في الإمارات، ورابطة العالم الإسلامي في المغرب العربي. قد تختلف بدقيقة أو دقيقتين عن التقويم الرسمي المحلي.",
        "all": "جميع المدن", "privacy": "الخصوصية", "geo": "بيانات المواقع",
        "estimate": "",
    },
    "bn": {
        "places": "places-bd.json", "source": Computed, "lang": "bn", "locale": "bn-BD", "og": "bn_BD",
        "full": "{name}",
        "store": "", "app_name": "Adhan Time", "full_month": True,
        "cols": ["ফজর", "সূর্যোদয়", "যোহর", "আসর", "মাগরিব", "এশা"], "sun": 1, "iftar": 4,
        "months": "জানুয়ারি ফেব্রুয়ারি মার্চ এপ্রিল মে জুন জুলাই আগস্ট সেপ্টেম্বর অক্টোবর নভেম্বর ডিসেম্বর".split(),
        "days": "সোমবার মঙ্গলবার বুধবার বৃহস্পতিবার শুক্রবার শনিবার রবিবার".split(),
        "days_short": "সোম মঙ্গল বুধ বৃহঃ শুক্র শনি রবি".split(),
        "compass": ["উত্তর", "উত্তর-পূর্ব", "পূর্ব", "দক্ষিণ-পূর্ব", "দক্ষিণ", "দক্ষিণ-পশ্চিম", "পশ্চিম", "উত্তর-পশ্চিম"],
        "next": "{n} শুরু হতে {d} বাকি", "h": "ঘণ্টা", "m": "মিনিট",
        "root": "নামাজের সময়সূচি",
        "title": "{name} নামাজের সময়সূচি আজ – {month} | Adhan Time",
        "desc": "আজ {name}-এ নামাজের সময়: ফজর, সূর্যোদয়, যোহর, আসর, মাগরিব ও এশা। {month} মাসের নামাজের সময়সূচি, কিবলার দিক এবং রমজান ২০২৭-এর সেহরি ও ইফতারের সময়সূচি।",
        "h1": "{name} নামাজের সময়সূচি",
        "lead": "{full}-এর নামাজের সময়। আজকের সময় এবং পরবর্তী নামাজ পর্যন্ত বাকি সময় নিচে; পুরো মাসের সময়সূচি টেবিলে।",
        "month_h": "{name} নামাজের সময়সূচি – {month}",
        "date_col": "তারিখ",
        "qibla_h": "{name} থেকে কিবলার দিক",
        "qibla": "{full} থেকে কিবলা উত্তর দিক থেকে ঘড়ির কাঁটার দিকে <b>{deg}°</b> ({compass} দিকে)। কাবা শরিফের দূরত্ব প্রায় <b>{km} কিমি</b>।",
        "others": "{group} বিভাগের অন্যান্য এলাকা",
        "ram_slug": "ramadan-sehri-iftar-2027",
        "ram_btn": "{name} রমজান ২০২৭ সেহরি ও ইফতারের সময়সূচি →",
        "ram_title": "{name} সেহরি ও ইফতারের সময়সূচি – রমজান ২০২৭",
        "ram_desc": "রমজান ১৪৪৮ হিজরি / ২০২৭-এ {full}-এর সেহরির শেষ সময় ও ইফতারের সময়, ৮ ফেব্রুয়ারি ২০২৭ থেকে প্রতিদিন। প্রথম দিন: সেহরি শেষ {imsak}, ইফতার {iftar}।",
        "ram_h1": "{name} সেহরি ও ইফতারের সময়সূচি – রমজান ২০২৭",
        "ram_lead": "রমজান ১৪৪৮ হিজরিতে {full}-এর সেহরির শেষ সময় (ফজর) ও ইফতারের সময় (মাগরিব)। সময়সূচিটি ৮ ফেব্রুয়ারি ২০২৭ থেকে রমজান শুরু ধরে তৈরি; বাংলাদেশে চাঁদ দেখার ওপর নির্ভর করে রমজান একদিন পরেও শুরু হতে পারে।",
        "ram_crumb": "রমজান ২০২৭",
        "ram_day": "রোজা", "ram_imsak_sub": "সেহরি শেষ", "ram_iftar_sub": "ইফতার",
        "fact_imsak": "প্রথম দিন সেহরি শেষ", "fact_iftar": "প্রথম দিন ইফতার", "fact_last": "শেষ ইফতার ({d})",
        "note_first": "প্রথম রোজা", "note_30": "মাস ৩০ দিনের হলে", "note_eid": "ঈদুল ফিতর",
        "ram_howto_h": "সময়সূচি কীভাবে পড়বেন",
        "ram_howto": "<b>ফজর</b>-এর সময় শুরু হলে সেহরির সময় শেষ হয়; সতর্কতার জন্য কয়েক মিনিট আগে খাওয়া শেষ করুন। <b>মাগরিব</b>-এর সময় ইফতার। তারাবির নামাজ এশার পরে আদায় করা হয়।",
        "back": "{name} দৈনিক নামাজের সময়সূচি →",
        "index_title": "বাংলাদেশের নামাজের সময়সূচি আজ | Adhan Time",
        "index_desc": "বাংলাদেশের সব বিভাগের শহরগুলোর আজকের নামাজের সময়সূচি, মাসিক সময়সূচি, কিবলার দিক এবং রমজান ২০২৭-এর সেহরি ও ইফতারের সময়।",
        "index_h1": "বাংলাদেশের নামাজের সময়সূচি",
        "index_lead": "{g}টি বিভাগের {n}টি এলাকার নামাজের সময়: আজকের সময়, মাসিক সময়সূচি, কিবলার দিক এবং রমজান ২০২৭-এর সময়সূচি। আপনার এলাকা বেছে নিন।",
        "ram_index_title": "রমজান ২০২৭ সেহরি ও ইফতারের সময়সূচি – বাংলাদেশ",
        "ram_index_desc": "রমজান ১৪৪৮ হিজরি / ২০২৭-এ বাংলাদেশের সব বিভাগের এলাকাগুলোর সেহরি ও ইফতারের সময়সূচি।",
        "ram_index_h1": "রমজান ২০২৭ সেহরি ও ইফতারের সময়সূচি",
        "ram_index_lead": "রমজান ১৪৪৮ হিজরি ৮ বা ৯ ফেব্রুয়ারি ২০২৭ শুরু হওয়ার কথা (চাঁদ দেখার ওপর নির্ভরশীল)। আপনার এলাকা বেছে নিন।",
        "app_h": "আজানের সময় নোটিফিকেশন পান",
        "app_p": "Adhan Time অ্যাপ আপনার অবস্থানের নামাজের সময় ইন্টারনেট ছাড়াই হিসাব করে এবং আজানের সুরে মনে করিয়ে দেয়; সঙ্গে আছে কিবলা কম্পাস, কুরআন, সেহরি-ইফতারের সময়সূচি ও সেহরির রিমাইন্ডার। বিনামূল্যে ও বিজ্ঞাপনমুক্ত।",
        "method": "সময় হিসাব করা হয়েছে করাচি বিশ্ববিদ্যালয়ের পদ্ধতিতে (ফজর ও এশা ১৮°, আসর হানাফি মাজহাব অনুযায়ী)। ইসলামিক ফাউন্ডেশনের সময়সূচির সঙ্গে ১–২ মিনিট পার্থক্য হতে পারে।",
        "all": "সব এলাকা", "privacy": "গোপনীয়তা নীতি", "geo": "অবস্থানের তথ্য",
        "estimate": "",
    },
    "en": {
        "places": "places-en.json", "source": Computed, "lang": "en", "locale": "en-GB", "og": "en_GB",
        "store": "", "app_name": "Adhan Time",
        "cols": ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"], "sun": 1, "iftar": 4,
        "months": "January February March April May June July August September October November December".split(),
        "days": "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split(),
        "days_short": "Mon Tue Wed Thu Fri Sat Sun".split(),
        "compass": ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"],
        "next": "{n} in {d}", "h": "h", "m": "min",
        "root": "Prayer Times",
        "title": "Prayer Times in {name} Today – {month} | Adhan Time",
        "desc": "Today's prayer times (namaz timings) in {name}: Fajr, Sunrise, Dhuhr, Asr, Maghrib and Isha. {month} prayer timetable, qibla direction and the Ramadan 2027 timetable.",
        "h1": "Prayer Times in {name}",
        "lead": "Salah times for {full}. Today's times and a countdown to the next prayer are below; the whole month is in the table.",
        "month_h": "{name} prayer timetable, {month}",
        "date_col": "Date",
        "qibla_h": "Qibla direction in {name}",
        "qibla": "From {full} the qibla is <b>{deg}°</b> clockwise from north ({compass}). The Kaaba is about <b>{km} km</b> away.",
        "others": "Other cities in {group}",
        "ram_slug": "ramadan-timetable-2027",
        "ram_btn": "{name} Ramadan 2027 timetable →",
        "ram_title": "Ramadan Timetable 2027 {name} – Sehri and Iftar Times",
        "ram_desc": "Ramadan 1448 AH / 2027 timetable for {full}: sehri (suhoor) ends at Fajr and iftar is at Maghrib, day by day from 8 February 2027. Day 1: Fajr {imsak}, iftar {iftar}.",
        "ram_h1": "Ramadan 2027 Timetable for {name}",
        "ram_lead": "Sehri (suhoor) end and iftar times in {full} for Ramadan 1448 AH. The timetable assumes Ramadan begins on Monday 8 February 2027, its astronomical start; depending on moon sighting it may begin a day later where you live.",
        "ram_crumb": "Ramadan 2027",
        "ram_day": "Day", "ram_imsak_sub": "sehri ends", "ram_iftar_sub": "iftar",
        "fact_imsak": "Sehri ends, day 1", "fact_iftar": "Iftar, day 1", "fact_last": "Last iftar ({d})",
        "note_first": "First fast", "note_30": "If Ramadan has 30 days", "note_eid": "Eid al-Fitr",
        "ram_howto_h": "How to read the timetable",
        "ram_howto": "The fast begins at <b>Fajr</b>: finish sehri a few minutes before it. Iftar is at <b>Maghrib</b>. Taraweeh is prayed after Isha.",
        "back": "Daily prayer times in {name} →",
        "index_title": "Prayer Times Today – Pakistan, UK, USA, Canada, Australia | Adhan Time",
        "index_desc": "Today's prayer times and namaz timings for cities in Pakistan, the United Kingdom, the United States, Canada and Australia, with monthly timetables, qibla direction and the Ramadan 2027 timetable.",
        "index_h1": "Prayer Times",
        "index_lead": "Prayer times for {n} cities in {g} countries: today's times, the monthly timetable, qibla direction and the Ramadan 2027 timetable. Choose your city.",
        "ram_index_title": "Ramadan Timetable 2027 – Sehri and Iftar Times by City",
        "ram_index_desc": "Ramadan 1448 AH / 2027 sehri and iftar timetables for cities in Pakistan, the UK, the US, Canada and Australia.",
        "ram_index_h1": "Ramadan 2027 Timetable",
        "ram_index_lead": "Ramadan 1448 AH is expected to begin on Monday 8 February 2027, subject to moon sighting. Choose your city for sehri and iftar times.",
        "app_h": "Get adhan notifications",
        "app_p": "The Adhan Time app works out the prayer times where you are, offline, and reminds you with the adhan; it also has a qibla compass, the Quran, a Ramadan timetable and sehri reminders. Free, with no ads.",
        "method": "Times are calculated with each country's usual method, as in the app: Karachi (University of Islamic Sciences) with Hanafi Asr in Pakistan, ISNA in the US and Canada and the Muslim World League elsewhere; where twilight never ends in summer, Fajr and Isha follow the angle-based rule. Local mosque timetables can differ by a few minutes.",
        "all": "All cities", "privacy": "Privacy", "geo": "Location data",
        "estimate": "",
    },
}


# ------------------------------------------------------------------ pages

class Site:
    def __init__(self, code, cfg, first):
        self.code, self.c, self.first = code, cfg, first
        self.base = f"/ezan/{code}/"
        self.src = cfg["source"]()
        self.groups = json.load(open(os.path.join(HERE, cfg["places"]), encoding="utf-8"))

    def month_name(self, d):
        return f"{self.c['months'][d.month - 1]} {d.year}"

    def long_date(self, d):
        return f"{self.c['days'][d.weekday()]}, {d.day} {self.c['months'][d.month - 1]} {d.year}"

    def short_date(self, d):
        month = self.c["months"][d.month - 1]
        return f"{d.day} {month if self.c.get('full_month') else month[:3]} {self.c['days_short'][d.weekday()]}"

    def path(self, p, ramadan=False):
        return f"{self.base}{p['slug']}/" + (f"{self.c['ram_slug']}/" if ramadan else "")

    def stores(self):
        c = self.c
        country = f"{c['store']}/" if c.get("store") else ""
        return (f"https://apps.apple.com/{country}app/id{APP_ID}",
                f"https://play.google.com/store/apps/details?id={PKG}&hl={c['lang']}")

    def page(self, path, title, desc, body, crumbs, tz):
        c = self.c
        crumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + h} for i, (n, h) in enumerate(crumbs)]}
        nav = " › ".join(f'<a href="{e(h)}">{e(n)}</a>' if i < len(crumbs) - 1 else f"<span>{e(n)}</span>"
                         for i, (n, h) in enumerate(crumbs))
        ios, play = self.stores()
        dir_attr = ' dir="rtl"' if c.get("rtl") else ""
        return f"""<!doctype html>
<html lang="{c['lang']}"{dir_attr}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{e(path)}">
<meta name="apple-itunes-app" content="app-id={APP_ID}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{e(path)}">
<meta property="og:image" content="{SITE}/img/ezan-vakti.png">
<meta property="og:locale" content="{c['og']}">
<meta name="theme-color" content="#1c876b">
<link rel="icon" href="/img/ezan-vakti.png">
<link rel="stylesheet" href="/ezan/site.css">
<script type="application/ld+json">{json.dumps(crumb_ld, ensure_ascii=False)}</script>
</head>
<body data-tz="{e(tz)}" data-locale="{c['locale']}" data-next="{e(c['next'])}" data-h="{e(c['h'])}" data-m="{e(c['m'])}">
<header class="top"><div class="wrap"><a class="logo" href="{self.base}"><img src="/img/ezan-vakti.png" alt="" width="28" height="28">{e(c['app_name'])}</a></div></header>
<main class="wrap">
<nav class="crumbs">{nav}</nav>
{body}
<section class="app">
<img src="/img/ezan-vakti.png" alt="{e(c['app_name'])}" width="64" height="64" loading="lazy">
<div>
<h2>{e(c['app_h'])}</h2>
<p>{e(c['app_p'])}</p>
<p class="stores"><a class="store" href="{ios}">App Store</a><a class="store" href="{play}">Google Play</a></p>
</div>
</section>
</main>
<footer class="wrap foot">
<p>{e(c['method'])}</p>
<p><a href="{self.base}">{e(c['all'])}</a> · <a href="{self.base}{c['ram_slug']}/">{e(c['ram_crumb'])}</a> · <a href="/">MuGi Labs</a> · <a href="/privacy.html">{e(c['privacy'])}</a></p>
<p class="small">{e(c['geo'])}: <a href="https://www.geonames.org/" rel="nofollow">GeoNames</a> (CC BY 4.0).</p>
{LANG_LINKS}
</footer>
<script src="/ezan/app.js" defer></script>
</body>
</html>
"""

    def table(self, rows, ramadan=False):
        c = self.c
        heads = []
        for i, col in enumerate(c["cols"]):
            sub = ""
            if ramadan and i == 0:
                sub = f"<br><small>{e(c['ram_imsak_sub'])}</small>"
            if ramadan and i == c["iftar"]:
                sub = f"<br><small>{e(c['ram_iftar_sub'])}</small>"
            heads.append(f"<th>{e(col)}{sub}</th>")
        first = f"<th>{e(c['ram_day'])}</th><th>{e(c['date_col'])}</th>" if ramadan else f"<th>{e(c['date_col'])}</th>"
        out = [f'<div class="tablewrap"><table class="times{" ram7" if ramadan else ""}"><thead><tr>{first}{"".join(heads)}</tr></thead><tbody>']
        for r in rows:
            d, ts = r["date"], r["times"]
            note = f'<span class="note">{e(r["note"])}</span>' if r.get("note") else ""
            lead = f'<td class="rd">{e(r["rday"])}</td>' if ramadan else ""
            cls = f' class="{r["cls"]}"' if r.get("cls") else ""
            key = (0, c["iftar"]) if ramadan else ()
            cells = "".join(f'<td class="k">{t}</td>' if i in key else f"<td>{t}</td>" for i, t in enumerate(ts))
            out.append(f'<tr data-d="{d.isoformat()}" data-t="{" ".join(ts)}"{cls}>{lead}<td class="d">{e(self.short_date(d))}{note}</td>{cells}</tr>')
        out.append("</tbody></table></div>")
        return "".join(out)

    def place(self, g, p, stamp):
        c = self.c
        first = self.first
        days = calendar.monthrange(first.year, first.month)[1]
        rows, est = [], False
        for i in range(days):
            d = first + timedelta(days=i)
            ts, x = self.src.day(p, d)
            est = est or x
            rows.append({"date": d, "times": ts})
        nxt = first + timedelta(days=days)
        after, _ = self.src.day(p, nxt)
        name, full = p["name"], c.get("full", "{name}, {group}").format(name=p["name"], group=g["name"])
        month = self.month_name(first)
        fmt = dict(name=name, full=full, month=month, zone=p.get("zone", ""), group=g["name"])
        h0 = rows[0]
        hero = "".join(f'<li data-n="{"sun" if i == c["sun"] else i}"><span>{e(col)}</span><b>{t}</b></li>'
                       for i, (col, t) in enumerate(zip(c["cols"], h0["times"])))
        seven = " seven" if len(c["cols"]) == 7 else ""
        bearing, dist = qibla(p["lat"], p["lon"])
        others = "".join(f'<li><a href="{self.path(o)}">{e(o["name"])}</a></li>' for o in g["places"] if o["slug"] != p["slug"])
        path = self.path(p)
        body = f"""<h1>{e(c['h1'].format(**fmt))}</h1>
<p class="lead">{e(c['lead'].format(**fmt))}</p>
<section class="hero" id="hero">
<p class="today"><span id="hero-date">{e(self.long_date(h0['date']))}</span> · {e(full)}</p>
<p class="next" id="next" hidden></p>
<ul class="six{seven}">{hero}</ul>
</section>
<p class="cta"><a class="btn" href="{self.path(p, True)}">{e(c['ram_btn'].format(**fmt))}</a></p>
<section><h2>{e(c['month_h'].format(**fmt))}</h2>
{self.table(rows)}<div hidden id="after" data-d="{nxt.isoformat()}" data-t="{" ".join(after)}"></div>
{f'<p class="small">{e(c["estimate"])}</p>' if est and c["estimate"] else ""}
</section>
<section class="info"><h2>{e(c['qibla_h'].format(**fmt))}</h2>
<p>{c['qibla'].format(full=e(full), deg=f"{bearing:.0f}", compass=c['compass'][int((bearing + 22.5) // 45) % 8], km=f"{dist:,.0f}".replace(",", "."))}</p>
</section>
{f'<section><h2>{e(c["others"].format(**fmt))}</h2><ul class="grid">{others}</ul></section>' if others else ""}"""
        crumbs = [(c["root"], self.base), (name, path)]
        return path, self.page(path, c["title"].format(**fmt), c["desc"].format(**fmt), body, crumbs, p["tz"])

    def ramadan(self, g, p):
        c = self.c
        rows, est = [], False
        days = self.src.ramadan(p)
        for i, (d, rday) in enumerate(days):
            ts, x = self.src.day(p, d, ramadan=rday != "–")
            est = est or x
            note, cls = "", ""
            if i == 0:
                note = c["note_first"]
            if rday == "30" and c["note_30"]:
                note = c["note_30"]
            if rday == "–":
                note, cls = c["note_eid"], "bayram"
            rows.append({"date": d, "times": ts, "rday": rday, "note": note, "cls": cls})
        fasting = [r for r in rows if r["rday"] != "–"]
        last = fasting[-1]
        name, full = p["name"], c.get("full", "{name}, {group}").format(name=p["name"], group=g["name"])
        fmt = dict(name=name, full=full, imsak=rows[0]["times"][0], iftar=rows[0]["times"][c["iftar"]])
        path = self.path(p, True)
        body = f"""<h1>{e(c['ram_h1'].format(**fmt))}</h1>
<p class="lead">{e(c['ram_lead'].format(**fmt))}</p>
<ul class="facts">
<li><span>{e(c['fact_imsak'])}</span><b>{rows[0]['times'][0]}</b></li>
<li><span>{e(c['fact_iftar'])}</span><b>{rows[0]['times'][c['iftar']]}</b></li>
<li><span>{e(c['fact_last'].format(d=f"{last['date'].day} {c['months'][last['date'].month - 1]}"))}</span><b>{last['times'][c['iftar']]}</b></li>
</ul>
{self.table(rows, ramadan=True)}
{f'<p class="small">{e(c["estimate"])}</p>' if est and c["estimate"] else ""}
<section class="info"><h2>{e(c['ram_howto_h'])}</h2>
<p>{c['ram_howto']}</p>
<p><a href="{self.path(p)}">{e(c['back'].format(**fmt))}</a></p>
</section>"""
        crumbs = [(c["root"], self.base), (name, self.path(p)), (c["ram_crumb"], path)]
        return path, self.page(path, c["ram_title"].format(**fmt), c["ram_desc"].format(**fmt), body, crumbs, p["tz"])

    def index(self, ramadan=False):
        c = self.c
        n = sum(len(g["places"]) for g in self.groups)
        parts = []
        for g in self.groups:
            items = "".join(f'<li><a href="{self.path(p, ramadan)}">{e(p["name"])}</a></li>' for p in g["places"])
            parts.append(f'<section><h2>{e(g["name"])}</h2><ul class="grid">{items}</ul></section>')
        if ramadan:
            path = f"{self.base}{c['ram_slug']}/"
            title, desc, h1, lead = c["ram_index_title"], c["ram_index_desc"], c["ram_index_h1"], c["ram_index_lead"]
            crumbs = [(c["root"], self.base), (c["ram_crumb"], path)]
            cta = ""
        else:
            path = self.base
            title, desc, h1, lead = c["index_title"], c["index_desc"], c["index_h1"], c["index_lead"]
            crumbs = [(c["root"], self.base)]
            cta = f'<p class="cta"><a class="btn" href="{self.base}{c["ram_slug"]}/">{e(c["ram_index_h1"])} →</a></p>'
        body = f"""<h1>{e(h1)}</h1>
<p class="lead">{e(lead.format(n=n, g=len(self.groups)))}</p>
{cta}
{"".join(parts)}"""
        tz = self.groups[0]["places"][0]["tz"]
        return path, self.page(path, title, desc, body, crumbs, tz)

    def all_pages(self, stamp):
        yield self.index()
        yield self.index(ramadan=True)
        for g in self.groups:
            for p in g["places"]:
                yield self.place(g, p, stamp)
                yield self.ramadan(g, p)


def pages(first, stamp):
    for code, cfg in LOCALES.items():
        yield from Site(code, cfg, first).all_pages(stamp)
