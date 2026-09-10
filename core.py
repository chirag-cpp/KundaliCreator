# -*- coding: utf-8 -*-
"""Core Jyotish engine: positions, panchanga, divisional charts, Jaimini."""
import math, unicodedata, datetime as dt
from zoneinfo import ZoneInfo
import swisseph as swe
from tables import *

swe.set_sid_mode(swe.SIDM_LAHIRI)
FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

# Swiss Ephemeris keeps the sidereal mode as global library state, and its
# default is mode 0 = Fagan-Bradley. Anything that resets that state (a
# swe.close(), a module reload, another library touching swisseph) would
# silently produce a Western-sidereal chart. So we re-assert the mode
# immediately before every calculation instead of trusting the import-time
# call, and verify it at runtime.
def _lahiri():
    swe.set_sid_mode(swe.SIDM_LAHIRI)

def ayanamsa_check(jd):
    """Return (name, value) and raise if the active mode is not Lahiri."""
    _lahiri()
    name = swe.get_ayanamsa_name(swe.SIDM_LAHIRI)
    val = swe.get_ayanamsa_ut(jd)
    ref = swe.get_ayanamsa_ut(swe.julday(2000, 1, 1, 12))
    # Lahiri is 23 deg 51' at J2000; Fagan-Bradley is 24 deg 44'. If the
    # library ignored our mode this guard catches it rather than shipping a
    # wrong chart.
    if not (23.5 < ref < 24.1):
        raise RuntimeError(
            f"Sidereal mode is not Lahiri (J2000 ayanamsa = {ref:.4f} deg, "
            f"expected ~23.857). The Swiss Ephemeris sidereal mode was reset "
            f"by something else in this process.")
    return name, val

PLANET_IDS = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,
    "Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN,
    "Rahu":swe.TRUE_NODE}

def norm(x): return x % 360.0

def dms(x, sign_rel=True):
    """Format degrees as D°M'S\" (within sign if sign_rel)."""
    if sign_rel: x = x % 30
    d = int(x); m = int((x-d)*60); s = int(round(((x-d)*60-m)*60))
    if s == 60: s = 0; m += 1
    if m == 60: m = 0; d += 1
    return f"{d:02d}°{m:02d}'{s:02d}\""

# ---------------------------------------------------------------- geocoding
def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower().strip()

def geocode_candidates(town, country=None, limit=8):
    """Return a ranked list of plausible matches for a place name.

    Matching is progressively looser so that small towns absent from the
    database still resolve to their nearest listed neighbour:
      1. exact name match
      2. the query contains a listed city name  ("Naya Nangal" -> "Nangal")
      3. a listed city name contains the query  ("Ghazi" -> "Ghaziabad")
      4. fuzzy match on spelling
    """
    import difflib, geonamescache
    gc = geonamescache.GeonamesCache()
    cities = list(gc.get_cities().values())
    if country:
        cc = country.strip().upper()
        sub = [c for c in cities if c["countrycode"] == cc]
        cities = sub or cities

    q = strip_accents(town)
    q_tokens = set(q.split())
    # Generic Indian place-name suffixes that must never match on their own.
    STOP = {"nagar", "pur", "puri", "ganj", "abad", "bagh", "vihar", "colony",
            "east", "west", "north", "south", "new", "naya", "town", "city",
            "khurd", "kalan", "road", "district", "tehsil", "village"}
    scored = []
    for c in cities:
        n = strip_accents(c["name"])
        if n == q:
            s = 0
        elif len(n) >= 4 and n not in STOP and n in q_tokens:
            s = 1                      # "Nangal" is a word of "Naya Nangal"
        elif len(n) >= 5 and n not in STOP and (n in q or q in n):
            s = 2                      # "Ghazi" <-> "Ghaziabad"
        else:
            continue
        scored.append((s, -c["population"], c))

    if not scored:                      # last resort: fuzzy spelling match
        names = {strip_accents(c["name"]): c for c in cities}
        for m in difflib.get_close_matches(q, names.keys(), n=limit, cutoff=0.75):
            scored.append((3, -names[m]["population"], names[m]))

    scored.sort(key=lambda t: (t[0], t[1]))
    out, seen = [], set()
    for _, _, c in scored:
        key = (c["name"], c["countrycode"])
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": c["name"], "country": c["countrycode"],
                    "lat": c["latitude"], "lon": c["longitude"],
                    "tz": c["timezone"], "population": c["population"]})
        if len(out) >= limit:
            break
    return out

def geocode(town, state=None, country=None):
    c = geocode_candidates(town, country, limit=1)
    if not c:
        raise ValueError(
            f"Could not match '{town}' to any place in the offline database. "
            "Try the nearest larger town, or enter latitude/longitude directly.")
    return c[0]

# ---------------------------------------------------------------- chart core
class Chart:
    def __init__(self, date_str, time_str, lat, lon, tzname, place_label="", name=None):
        self.name = name
        self.place_label = place_label
        self.lat, self.lon = lat, lon
        self.tzname = tzname
        local = dt.datetime.fromisoformat(f"{date_str}T{time_str}")
        self.local = local.replace(tzinfo=ZoneInfo(tzname))
        u = self.local.astimezone(dt.timezone.utc)
        self.utc = u
        self.jd = swe.julday(u.year, u.month, u.day,
                             u.hour + u.minute/60 + u.second/3600)
        self.ayanamsa_name, self.ayanamsa = ayanamsa_check(self.jd)
        self._positions()
        self._lagna()
        self._sunrise()

    def _positions(self):
        _lahiri()
        self.pos, self.speed = {}, {}
        for p, pid in PLANET_IDS.items():
            xx, _ = swe.calc_ut(self.jd, pid, FLAGS)
            self.pos[p] = norm(xx[0]); self.speed[p] = xx[3]
        self.pos["Ketu"] = norm(self.pos["Rahu"] + 180)
        self.speed["Ketu"] = self.speed["Rahu"]

    def _lagna(self):
        _lahiri()
        cusps, ascmc = swe.houses_ex(self.jd, self.lat, self.lon, b'W',
                                     swe.FLG_SIDEREAL)
        self.asc = norm(ascmc[0])
        self.mc = norm(ascmc[1])
        self.asc_sign = int(self.asc // 30)

    def _sunrise(self):
        geo = (self.lon, self.lat, 0)
        flag = swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
        # search back from birth time to find the sunrise governing this Vedic day
        try:
            r = swe.rise_trans(self.jd - 1.2, swe.SUN, flag, geo)
            jr = r[1][0]
            while True:
                nxt = swe.rise_trans(jr + 0.01, swe.SUN, flag, geo)[1][0]
                if nxt > self.jd: break
                jr = nxt
            self.jd_sunrise = jr
            nxt_set = swe.rise_trans(jr, swe.SUN, swe.CALC_SET |
                        swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geo)[1][0]
            self.jd_sunset = nxt_set
            self.jd_next_sunrise = swe.rise_trans(jr + 0.6, swe.SUN, flag, geo)[1][0]
        except Exception:
            # polar fallback: 6 AM local
            self.jd_sunrise = self.jd - ((self.local.hour-6)/24)
            self.jd_sunset = self.jd_sunrise + 0.5
            self.jd_next_sunrise = self.jd_sunrise + 1

    # ----- basic accessors
    def sign_of(self, lon): return int(norm(lon) // 30)
    def deg_in_sign(self, lon): return norm(lon) % 30

    def house_of(self, lon, asc_sign=None):
        a = self.asc_sign if asc_sign is None else asc_sign
        return (self.sign_of(lon) - a) % 12 + 1

    # ----- nakshatra
    def nakshatra(self, lon):
        idx = int(norm(lon) // (360/27))
        pada = int((norm(lon) % (360/27)) // (360/108)) + 1
        frac = (norm(lon) % (360/27)) / (360/27)
        return idx, pada, frac

    # ----- panchanga
    def panchanga(self):
        sun, moon = self.pos["Sun"], self.pos["Moon"]
        diff = norm(moon - sun)
        t = int(diff // 12) + 1                      # tithi 1..30
        paksha = "Shukla" if t <= 15 else "Krishna"
        tn = t if t <= 15 else t - 15
        if tn == 15:
            tname = "Purnima" if paksha == "Shukla" else "Amavasya"
        else:
            tname = TITHIS[tn-1]
        yoga = YOGAS[int(norm(sun + moon) // (360/27))]
        # karana: 60 half-tithis
        k = int(diff // 6)
        if k == 0: kar = "Kimstughna"
        elif k >= 57: kar = KARANAS_FIXED[k-57]
        else: kar = KARANAS_MOVABLE[(k-1) % 7]
        # Vedic weekday runs sunrise->sunrise: use the governing sunrise moment
        y, m, d_, h_ = swe.revjul(self.jd_sunrise)
        sr_utc = dt.datetime(y, m, d_, tzinfo=dt.timezone.utc) + \
                 dt.timedelta(hours=h_)
        weekday = sr_utc.astimezone(ZoneInfo(self.tzname)).strftime("%A")
        return {"tithi": f"{paksha} {tname}", "tithi_num": t, "paksha": paksha,
                "yoga": yoga, "karana": kar, "weekday": weekday}

    # ----- divisional charts ------------------------------------------------
    def varga_sign(self, lon, d):
        s = self.sign_of(lon); deg = self.deg_in_sign(lon)
        odd = (s % 2 == 0)          # Aries=0 is odd sign
        movable, fixed, dual = (s % 3 == 0), (s % 3 == 1), (s % 3 == 2)
        if d == 1: return s
        if d == 2:   # Hora: Sun(Leo)/Moon(Cancer)
            if odd: return 4 if deg < 15 else 3
            return 3 if deg < 15 else 4
        if d == 3: return (s + [0,4,8][int(deg//10)]) % 12
        if d == 4: return (s + [0,3,6,9][int(deg//7.5)]) % 12
        if d == 7:
            part = int(deg // (30/7))
            return ((s if odd else s+6) + part) % 12
        if d == 9:
            part = int(deg // (30/9))
            return self._d9(s, part)   # fire->Ar, earth->Cp, air->Li, water->Cn
        if d == 10:
            part = int(deg // 3)
            return ((s if odd else s+8) + part) % 12
        if d == 12: return (s + int(deg // 2.5)) % 12
        if d == 16:
            part = int(deg // (30/16))
            start = 0 if movable else (4 if fixed else 8)
            return (start + part) % 12
        if d == 20:
            part = int(deg // 1.5)
            start = 0 if movable else (8 if fixed else 4)
            return (start + part) % 12
        if d == 24:
            part = int(deg // 1.25)
            return ((4 if odd else 3) + part) % 12
        if d == 27:
            part = int(deg // (30/27))
            start = [0,3,6,9][s % 4]   # fire->Ar, earth->Cn, air->Li, water->Cp
            return (start + part) % 12
        if d == 30:
            if odd:
                bounds = [(5,0),(10,10),(18,8),(25,2),(30,6)]  # Ar,Aq,Sg,Ge,Li
            else:
                bounds = [(5,1),(12,5),(20,11),(25,9),(30,7)]  # Ta,Vi,Pi,Cp,Sc
            for b, sg in bounds:
                if deg < b: return sg
            return bounds[-1][1]
        if d == 40:
            part = int(deg // 0.75)
            return ((0 if odd else 6) + part) % 12
        if d == 45:
            part = int(deg // (30/45))
            start = 0 if movable else (4 if fixed else 8)
            return (start + part) % 12
        if d == 60:
            part = int(deg * 2)
            return (s + part) % 12
        raise ValueError(d)

    def _d9(self, s, part):
        start = [0, 9, 6, 3][s % 4]
        return (start + part) % 12

    def varga_chart(self, d):
        """Return dict: varga lagna sign, planet varga signs/houses, houses."""
        vl = self.varga_sign(self.asc, d)
        planets = {p: self.varga_sign(self.pos[p], d) for p in PLANETS9}
        houses = {h: [] for h in range(1, 13)}
        for p, sg in planets.items():
            houses[(sg - vl) % 12 + 1].append(p)
        return {"lagna_sign": vl, "planet_signs": planets,
                "planet_houses": {p: (sg - vl) % 12 + 1 for p, sg in planets.items()},
                "houses": houses,
                "house_signs": {h: (vl + h - 1) % 12 for h in range(1, 13)},
                "house_lords": {h: SIGN_LORDS[(vl + h - 1) % 12] for h in range(1, 13)}}

    # ----- aspects (user-specified rules) -----------------------------------
    def aspects(self):
        out = {}
        for p in PLANETS9:
            h = self.house_of(self.pos[p])
            out[p] = {"from_house": h,
                      "aspects_houses": sorted(((h - 1 + a - 1) % 12) + 1
                                               for a in DRISHTI[p])}
        return out

    # ----- Chara Karakas (7-scheme) ----------------------------------------
    def chara_karakas(self):
        degs = sorted(((self.deg_in_sign(self.pos[p]), p) for p in PLANETS7),
                      reverse=True)
        return [(KARAKA_NAMES[i], p, d) for i, (d, p) in enumerate(degs)]

    # ----- Arudha padas -----------------------------------------------------
    def arudha(self, house):
        """Arudha of `house` (1..12) with standard exception."""
        hsign = (self.asc_sign + house - 1) % 12
        lord = SIGN_LORDS[hsign]
        lsign = self.sign_of(self.pos[lord])
        cnt = (lsign - hsign) % 12          # lord is cnt+1 houses from house
        pada = (lsign + cnt) % 12
        rel = (pada - hsign) % 12 + 1
        if rel in (1, 7):                    # exception: take 10th therefrom
            pada = (pada + 9) % 12
        return pada

    # ----- Argala -----------------------------------------------------------
    def argala(self, ref_sign):
        """Primary argala (2,4,11) and virodha (12,10,3) on a sign."""
        occ = {s: [] for s in range(12)}
        for p in PLANETS9:
            occ[self.sign_of(self.pos[p])].append(p)
        arg, vir = {}, {}
        for a, v in ((2, 12), (4, 10), (11, 3)):
            arg[a] = occ[(ref_sign + a - 1) % 12]
            vir[a] = occ[(ref_sign + v - 1) % 12]
        return arg, vir

    # ----- Special Lagnas ---------------------------------------------------
    def special_lagnas(self):
        _lahiri()
        sun_rise = norm(swe.calc_ut(self.jd_sunrise, swe.SUN, FLAGS)[0][0])
        ghatis = (self.jd - self.jd_sunrise) * 60.0          # 1 day = 60 ghatis
        bl = norm(sun_rise + ghatis * 6)        # 1 sign / 5 ghatis
        hl = norm(sun_rise + ghatis * 12)       # 1 sign / 2.5 ghatis
        gl = norm(sun_rise + ghatis * 30)       # 1 sign / ghati
        vl = norm(sun_rise + ghatis * 60 * 30)  # 1 sign / vighati
        # Indu Lagna
        l9_lagna = SIGN_LORDS[(self.asc_sign + 8) % 12]
        moon_sign = self.sign_of(self.pos["Moon"])
        l9_moon = SIGN_LORDS[(moon_sign + 8) % 12]
        total = INDU_KALA[l9_lagna] + INDU_KALA[l9_moon]
        rem = total % 12
        if rem == 0: rem = 12
        indu_sign = (moon_sign + rem - 1) % 12
        return {"Bhava Lagna": bl, "Hora Lagna": hl, "Ghati Lagna": gl,
                "Vighati Lagna": vl, "Indu Lagna": indu_sign,
                "ghatis_elapsed": ghatis}
