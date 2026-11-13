"""Prayer-time calculation for the Ezan Vakti web pages.

A port of the app's PrayerTimeCalculator.swift (same angles per method, times shown as HH:mm with
the seconds dropped), except for the Diyanet method: that one follows Diyanet's own takvim more
closely than the app does (see _diyanet_solar; check_diyanet.py measures it against the official site).
"""
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

NAMES = ("imsak", "gunes", "ogle", "ikindi", "aksam", "yatsi")

# Same table as CalcMethod.params in the app: fajr angle, isha angle, isha interval (min), maghrib angle.
METHODS = {
    "diyanet": (18, 17, None, None),
    "mwl": (18, 17, None, None),
    "isna": (15, 15, None, None),
    "egypt": (19.5, 17.5, None, None),
    "karachi": (18, 18, None, None),
    "ummalqura": (18.5, 0, 90, None),
    "muis": (20, 18, None, None),
    "jakim": (20, 18, None, None),
    "kemenag": (20, 18, None, None),
    "dubai": (18.2, 18.2, None, None),
    "uoif": (12, 12, None, None),
    "russia": (16, 15, None, None),
}

# Corrections that make a method follow an authority's published timetable (fitted with the
# fit scripts against the official data): horizon angles for sunrise/sunset and offsets in seconds
# (rounding and ihtiyat). Kemenag (Indonesia, via api.myquran.com, 12 cities x 2026): ~90% of times
# to the minute, the rest 1 minute off; Kemenag also lowers the horizon for high cities (elevation).
TUNING = {
    "kemenag": {
        "angles": {"gunes": 0.95, "aksam": 1.0},
        "offsets": {"imsak": 180, "gunes": -135, "ogle": 240, "ikindi": 180, "aksam": 180, "yatsi": 180},
        "elevation": True,
    },
}

# Kemenag / JAKIM / MUIS publish a separate "Imsak" 10 minutes before Subuh (app: Ramadan.sahurEnd).
SEPARATE_IMSAK = {"kemenag", "jakim", "muis"}


def _dtr(d):
    return d * math.pi / 180


def _rtd(r):
    return r * 180 / math.pi


def _fix_hour(h):
    x = math.fmod(h, 24)
    return x + 24 if x < 0 else x


def _julian_day(year, month, day):
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5


def _sun_position(jd):
    d = jd - 2451545.0
    mean_anomaly = math.fmod(357.529 + 0.98560028 * d, 360)
    mean_long = math.fmod(280.459 + 0.98564736 * d, 360)
    ecl_long = math.fmod(mean_long + 1.915 * math.sin(_dtr(mean_anomaly)) + 0.020 * math.sin(_dtr(2 * mean_anomaly)), 360)
    obliquity = 23.439 - 0.00000036 * d
    right_asc = _fix_hour(_rtd(math.atan2(math.cos(_dtr(obliquity)) * math.sin(_dtr(ecl_long)), math.cos(_dtr(ecl_long)))) / 15)
    decl = _rtd(math.asin(math.sin(_dtr(obliquity)) * math.sin(_dtr(ecl_long))))
    eq_time = mean_long / 15 - right_asc
    return decl, eq_time


# Diyanet's published takvim, reverse-engineered (check_diyanet.py): the sun's declination and the
# equation of time are taken once per day at 0h UT (not at each prayer's moment), with these angles
# and per-vakit offsets in seconds (the temkin). Fitted on 11 provinces x 288 days of 2026: about 95%
# of the times match namazvakitleri.diyanet.gov.tr to the minute, the rest are 1 minute off.
DIYANET_ANGLES = {"imsak": 18.02, "gunes": 0.825, "aksam": 0.825, "yatsi": 17.02}
DIYANET_OFFSETS = {"imsak": 40, "gunes": -390, "ogle": 330, "ikindi": 275, "aksam": 455, "yatsi": 25}


def _diyanet_solar(day, lat, asr_factor):
    decl, eq = _sun_position(_julian_day(day.year, day.month, day.day))
    noon = _fix_hour(12.0 - eq)

    def hour_angle(angle):
        num = -math.sin(_dtr(angle)) - math.sin(_dtr(decl)) * math.sin(_dtr(lat))
        den = math.cos(_dtr(decl)) * math.cos(_dtr(lat))
        return _rtd(math.acos(min(max(num / den, -1), 1))) / 15.0

    asr_angle = -_rtd(math.atan(1.0 / (asr_factor + math.tan(_dtr(abs(lat - decl))))))
    solar = {
        "imsak": noon - hour_angle(DIYANET_ANGLES["imsak"]),
        "gunes": noon - hour_angle(DIYANET_ANGLES["gunes"]),
        "ogle": noon,
        "ikindi": noon + hour_angle(asr_angle),
        "aksam": noon + hour_angle(DIYANET_ANGLES["aksam"]),
        "yatsi": noon + hour_angle(DIYANET_ANGLES["yatsi"]),
    }
    return solar, DIYANET_OFFSETS


def times(day: date, lat: float, lon: float, tz: str, method: str = "diyanet", hanafi_asr: bool = False,
          elevation: float = 0.0, tuned: bool = True):
    """The six times of `day` as timezone-aware datetimes, keyed by NAMES (plus "subuh" when the
    method has a separate Imsak: then "imsak" is Subuh - 10 min and "subuh" the Fajr time)."""
    fajr_angle, isha_angle, isha_interval, maghrib_angle = METHODS[method]
    asr_factor = 2.0 if hanafi_asr else 1.0
    zone = ZoneInfo(tz)
    jd = _julian_day(day.year, day.month, day.day) - lon / (15.0 * 24.0)
    # The app reads the UTC offset at the moment it is called with (noon of the day is what the
    # pages use); DST switches happen at night, so noon gives the offset in force for the times.
    noon = datetime(day.year, day.month, day.day, 12, tzinfo=zone)
    tz_hours = noon.utcoffset().total_seconds() / 3600.0

    def mid_day(guess):
        _, eq = _sun_position(jd + guess)
        return _fix_hour(12.0 - eq)

    def sun_angle_time(angle, guess, ccw):
        decl, _ = _sun_position(jd + guess)
        num = -math.sin(_dtr(angle)) - math.sin(_dtr(decl)) * math.sin(_dtr(lat))
        den = math.cos(_dtr(decl)) * math.cos(_dtr(lat))
        ratio = min(max(num / den, -1), 1)
        t = _rtd(math.acos(ratio)) / 15.0
        return mid_day(guess) + (-t if ccw else t)

    def asr_time(guess):
        decl, _ = _sun_position(jd + guess)
        angle = -_rtd(math.atan(1.0 / (asr_factor + math.tan(_dtr(abs(lat - decl))))))
        return sun_angle_time(angle, guess, False)

    tuning = TUNING.get(method, {}) if tuned else {}
    t_angles = tuning.get("angles", {})
    # Horizon dip for cities well above the sea (Kemenag uses the city's height).
    dip = 0.0347 * math.sqrt(elevation) if tuning.get("elevation") and elevation >= 300 else 0.0
    edge = 0.833
    solar = {}
    solar["ogle"] = mid_day(0.5)
    solar["gunes"] = sun_angle_time(t_angles.get("gunes", edge) + dip, 0.25, True)
    maghrib = sun_angle_time(maghrib_angle if maghrib_angle is not None else t_angles.get("aksam", edge) + dip, 0.75, False)
    solar["aksam"] = maghrib
    solar["imsak"] = sun_angle_time(fajr_angle, 5.0 / 24.0, True)
    solar["yatsi"] = maghrib + isha_interval / 60.0 if isha_interval is not None else sun_angle_time(isha_angle, 18.0 / 24.0, False)
    solar["ikindi"] = asr_time(13.0 / 24.0)

    temkin = tuning.get("offsets", {})
    if method == "diyanet":
        solar, temkin = _diyanet_solar(day, lat, asr_factor)
    adjust = tz_hours - lon / 15.0
    start = datetime(day.year, day.month, day.day, tzinfo=zone)
    out = {}
    for name in NAMES:
        local = _fix_hour(solar[name] + adjust)
        seconds = math.floor(local * 3600 + 0.5 + temkin.get(name, 0))
        # Same as the app: start of day + seconds (wall-clock arithmetic is fine away from DST nights).
        out[name] = start + timedelta(seconds=seconds)
    if method in SEPARATE_IMSAK:
        out["subuh"] = out["imsak"]
        out["imsak"] = out["imsak"] - timedelta(minutes=10)
    return out


def hhmm(dt):
    """HH:mm with seconds dropped, as the app's DateFormatter shows it."""
    return dt.strftime("%H:%M")
