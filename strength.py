# -*- coding: utf-8 -*-
"""Shadbala, Bhava Bala, Ashtakavarga (values in virupas; 60 virupa = 1 rupa)."""
import math
import swisseph as swe
from tables import *
from core import norm

SAPTAVARGA = [1, 2, 3, 7, 9, 12, 30]
BENEFIC = {"Jupiter", "Venus"}          # Mercury/Moon conditional; simplified fixed
MALEFIC = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

def _relation(p, q):
    """Compound (panchadha) relation value keys for saptavargaja bala."""
    nat = 1 if q in FRIENDS.get(p, []) else (-1 if q in ENEMIES.get(p, []) else 0)
    return nat

def _temporal(chart, p, q):
    """Temporary friend if q sits 2,3,4,10,11,12 from p's sign."""
    d = (chart.sign_of(chart.pos[q]) - chart.sign_of(chart.pos[p])) % 12 + 1
    return 1 if d in (2, 3, 4, 10, 11, 12) else -1

def compound_relation(chart, p, sign):
    """Relation of planet p to the lord of `sign` -> virupa for saptavargaja."""
    lord = SIGN_LORDS[sign]
    if lord == p:
        return None  # own handled by caller
    nat, tmp = _relation(p, lord), _temporal(chart, p, lord)
    v = nat + tmp
    return {2: 22.5, 1: 15.0, 0: 7.5, -1: 3.75, -2: 1.875}[v]

def sthana_bala(chart, p):
    lon = chart.pos[p]
    # 1. Uccha bala
    ex_s, ex_d = EXALT[p]
    deep_ex = ex_s * 30 + ex_d
    dist = abs(norm(lon) - norm(deep_ex + 180))
    if dist > 180: dist = 360 - dist
    uccha = dist / 3.0
    # 2. Saptavargaja
    sv = 0.0
    for d in SAPTAVARGA:
        vs = chart.varga_sign(lon, d)
        mt = MOOLATRIKONA.get(p)
        if d == 1 and mt and vs == mt[0] and mt[1] <= chart.deg_in_sign(lon) <= mt[2]:
            sv += 45.0
        elif vs in OWN_SIGNS.get(p, []):
            sv += 30.0
        else:
            sv += compound_relation(chart, p, vs) or 30.0
    # 3. Ojayugma (D1 + D9): Moon/Venus even signs, others odd
    oj = 0.0
    for vs in (chart.sign_of(lon), chart.varga_sign(lon, 9)):
        even = vs % 2 == 1
        if p in ("Moon", "Venus"):
            oj += 15.0 if even else 0.0
        else:
            oj += 15.0 if not even else 0.0
    # 4. Kendradi
    h = chart.house_of(lon)
    kendradi = 60.0 if h in (1,4,7,10) else (30.0 if h in (2,5,8,11) else 15.0)
    # 5. Drekkana
    drek = int(chart.deg_in_sign(lon) // 10)  # 0,1,2
    dgroup = {"Sun":0,"Mars":0,"Jupiter":0,"Moon":1,"Venus":1,"Mercury":2,"Saturn":2}
    drekkana = 15.0 if drek == dgroup[p] else 0.0
    return {"Uccha": uccha, "Saptavargaja": sv, "Ojayugma": oj,
            "Kendradi": kendradi, "Drekkana": drekkana,
            "total": uccha + sv + oj + kendradi + drekkana}

def dig_bala(chart, p):
    strongest = {"Sun": chart.mc, "Mars": chart.mc,
                 "Jupiter": chart.asc, "Mercury": chart.asc,
                 "Moon": norm(chart.mc + 180), "Venus": norm(chart.mc + 180),
                 "Saturn": norm(chart.asc + 180)}[p]
    d = abs(norm(chart.pos[p]) - strongest)
    if d > 180: d = 360 - d
    return (180 - d) / 3.0

def kala_bala(chart, p):
    lon = chart.pos[p]
    out = {}
    # Nathonnatha (day/night)
    day = chart.jd_sunrise <= chart.jd < chart.jd_sunset
    if day:
        frac = (chart.jd - chart.jd_sunrise) / (chart.jd_sunset - chart.jd_sunrise)
        unnata = abs(frac - 0.5) * 2      # 1 at sunrise/set... midday=0
        midday_str = (1 - unnata) * 60
    else:
        end = chart.jd_next_sunrise
        start = chart.jd_sunset if chart.jd >= chart.jd_sunset else \
                chart.jd_sunset - 1
        frac = (chart.jd - start) / (end - start)
        midnight_str = (1 - abs(frac - 0.5) * 2) * 60
        midday_str = 60 - midnight_str
    nathonnatha = {"Moon": 60 - midday_str, "Mars": 60 - midday_str,
                   "Saturn": 60 - midday_str, "Sun": midday_str,
                   "Jupiter": midday_str, "Venus": midday_str,
                   "Mercury": 60.0}[p]
    out["Nathonnatha"] = nathonnatha
    # Paksha bala
    elong = norm(chart.pos["Moon"] - chart.pos["Sun"])
    if elong > 180: elong = 360 - elong
    pb = elong / 3.0
    if p in BENEFIC or p == "Moon" or (p == "Mercury"):
        val = pb
    else:
        val = 60 - pb
    if p == "Moon": val *= 2
    out["Paksha"] = val
    # Tribhaga
    tri = 0.0
    if day:
        third = int((chart.jd - chart.jd_sunrise) /
                    ((chart.jd_sunset - chart.jd_sunrise) / 3))
        tri_lord = ["Mercury", "Sun", "Saturn"][min(third, 2)]
    else:
        span = chart.jd_next_sunrise - chart.jd_sunset
        base = chart.jd_sunset if chart.jd >= chart.jd_sunset else chart.jd_sunset - 1
        third = int((chart.jd - base) / (span / 3))
        tri_lord = ["Moon", "Venus", "Mars"][min(third, 2)]
    if p == "Jupiter" or p == tri_lord: tri = 60.0
    out["Tribhaga"] = tri
    # Abda (year), Masa (month), Vara (weekday), Hora lords
    out["Abda"] = 15.0 if p == chart.abda_lord else 0.0
    out["Masa"] = 30.0 if p == chart.masa_lord else 0.0
    out["Vara"] = 45.0 if p == chart.vara_lord else 0.0
    out["Hora"] = 60.0 if p == chart.hora_lord else 0.0
    # Ayana bala (declination-based)
    xx, _ = swe.calc_ut(chart.jd, {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,
        "Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,
        "Saturn":swe.SATURN}[p], swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
    decl = xx[1]
    kranti = decl
    if p in ("Moon", "Saturn"):
        ab = (24 - kranti) * 60 / 48 if False else ((24 - kranti) / 48) * 60
    elif p == "Mercury":
        ab = ((24 + abs(kranti)) / 48) * 60
    else:  # Sun, Mars, Jupiter, Venus stronger in north declination
        ab = ((24 + kranti) / 48) * 60
    if p == "Sun": ab *= 2
    out["Ayana"] = max(0.0, min(ab, 120.0 if p == "Sun" else 60.0))
    out["total"] = sum(v for k, v in out.items() if k != "total")
    return out

# Cheshta bala via 8-fold motion classification (Vakradi bala)
CHESHTA_TABLE = {"Vakra":60,"Anuvakra":30,"Vikala":15,"Manda":15,
                 "Mandatara":7.5,"Sama":30,"Chara":45,"Atichara":30}
MEAN_SPEED = {"Mars":0.524,"Mercury":1.383,"Jupiter":0.083,
              "Venus":1.2,"Saturn":0.034}

def cheshta_bala(chart, p, kala, sthana):
    if p == "Sun":
        return None  # Ayana bala serves as Sun's cheshta (already in Kala)
    if p == "Moon":
        return None  # Paksha bala serves as Moon's cheshta
    sp, mean = chart.speed[p], MEAN_SPEED[p]
    if sp < 0:
        motion = "Vakra" if sp < -0.1 * mean else "Anuvakra"
    elif sp < 0.05 * mean:
        motion = "Vikala"
    elif sp < 0.5 * mean:
        motion = "Mandatara"
    elif sp < mean:
        motion = "Manda"
    elif sp < 1.25 * mean:
        motion = "Sama"
    elif sp < 2 * mean:
        motion = "Chara"
    else:
        motion = "Atichara"
    return {"motion": motion, "value": CHESHTA_TABLE[motion]}

def sputa_drishti(dist, aspecting):
    """BPHS graded aspect value of `aspecting` planet at angular dist (deg)."""
    d = dist % 360
    def base(d):
        if d < 30: return 0
        if d < 60: return (d - 30) / 2
        if d < 90: return 15 + (d - 60)
        if d < 120: return 45 - (d - 90) / 2
        if d < 150: return 30 - (d - 120)
        if d < 180: return (d - 150) * 2
        if d < 300: return 60 - (d - 180) / 2
        return 0
    v = base(d)
    if aspecting == "Mars" and (85 <= d <= 95 or 205 <= d <= 215): v = 60
    if aspecting == "Saturn" and (55 <= d <= 65 or 265 <= d <= 275): v = 60
    if aspecting == "Jupiter" and (115 <= d <= 125 or 235 <= d <= 245): v = 60
    return v

def drik_bala(chart, p):
    tot = 0.0
    for q in PLANETS7:
        if q == p: continue
        d = norm(chart.pos[p] - chart.pos[q])
        v = sputa_drishti(d, q)
        tot += v if q in BENEFIC or q == "Moon" or q == "Mercury" else -v
    return tot / 4.0

def shadbala(chart):
    res = {}
    for p in PLANETS7:
        st = sthana_bala(chart, p)
        dg = dig_bala(chart, p)
        ka = kala_bala(chart, p)
        ch = cheshta_bala(chart, p, ka, st)
        na = NAISARGIKA[p]
        dr = drik_bala(chart, p)
        chv = ch["value"] if ch else (ka["Ayana"] if p == "Sun" else ka["Paksha"] / 2)
        total = st["total"] + dg + ka["total"] + chv + na + dr
        # Sun/Moon: cheshta already counted inside kala; avoid double count
        if p in ("Sun", "Moon"):
            total = st["total"] + dg + ka["total"] + na + dr
        rupas = total / 60.0
        req = REQUIRED_VIRUPA[p] / 60.0
        res[p] = {"Sthana": st, "Dig": dg, "Kala": ka,
                  "Cheshta": ch, "Naisargika": na, "Drik": dr,
                  "total_virupa": total, "total_rupa": rupas,
                  "required_rupa": req, "ratio": rupas / req}
    ranked = sorted(res, key=lambda p: -res[p]["total_rupa"])
    for i, p in enumerate(ranked, 1):
        res[p]["rank"] = i
    return res

# ------------------------------------------------------------- Bhava Bala
def bhava_bala(chart, sb):
    """Per-house strength: lord's shadbala + bhava dig bala + bhava drik bala."""
    res = {}
    for h in range(1, 13):
        sign = (chart.asc_sign + h - 1) % 12
        lord = SIGN_LORDS[sign]
        adhipati = sb[lord]["total_virupa"]
        # Bhava dig bala (BPHS): classification of sign vs house position
        # Nara(human) signs strong in Lagna, Jalachara in 4th, Chatushpada 10th,
        # Keeta in 7th.
        NARA = {2, 5, 6, 10}; JALA = {3, 11}; KEETA = {7}
        CHATUS = {0, 1, 4, 9}  # (Sag/ Cap mixed: treated whole for simplicity)
        if sign in NARA: strong = 1
        elif sign in JALA: strong = 4
        elif sign in KEETA: strong = 7
        else: strong = 10
        dist = min((h - strong) % 12, (strong - h) % 12)
        bdig = max(0.0, 60 - dist * 10)
        # Bhava drishti bala on cusp (whole-sign midpoint)
        cusp = sign * 30 + 15.0
        bdrik = 0.0
        for q in PLANETS7:
            d = norm(cusp - chart.pos[q])
            v = sputa_drishti(d, q)
            bdrik += v if q in BENEFIC or q in ("Moon", "Mercury") else -v
        bdrik /= 4.0
        total = adhipati + bdig + bdrik
        res[h] = {"lord": lord, "Bhavadhipati": adhipati, "BhavaDig": bdig,
                  "BhavaDrik": bdrik, "total": total, "rupa": total / 60.0}
    ranked = sorted(res, key=lambda h: -res[h]["total"])
    for i, h in enumerate(ranked, 1):
        res[h]["rank"] = i
    return res

# ------------------------------------------------------------- Ashtakavarga
def ashtakavarga(chart):
    bav = {}
    for planet, table in BAV.items():
        bins = [0] * 12  # per sign
        for contrib, houses in table.items():
            base = chart.asc_sign if contrib == "Lagna" else \
                   chart.sign_of(chart.pos[contrib])
            for h in houses:
                bins[(base + h - 1) % 12] += 1
        bav[planet] = bins
    sav = [sum(bav[p][s] for p in bav) for s in range(12)]
    return bav, sav
