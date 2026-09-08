# -*- coding: utf-8 -*-
"""
Kundali text-report generator.

Usage:
  python3 generate_kundali.py --dob 1990-05-15 --time 14:30 --place "Ghaziabad" \
      [--state "Uttar Pradesh"] [--country IN] [--name "Full Name"] [--out file.txt]
  python3 generate_kundali.py --dob ... --time ... --lat 28.67 --lon 77.42 \
      --tz Asia/Kolkata --place-label "Ghaziabad, UP"

Ayanamsa: Lahiri (Chitrapaksha). Houses: whole-sign.
"""
import argparse, datetime as dt
from tables import *
from core import Chart, geocode, dms, norm
from strength import shadbala, bhava_bala, ashtakavarga
from dasha import vimshottari

L = []
def w(s=""): L.append(s)
def hr(c="="): w(c * 78)
def sec(title):
    w(); hr(); w(title.upper().center(78)); hr()

def digit_sum(n):
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(c) for c in str(n))
    return n

def name_number(name, table):
    return digit_sum(sum(table.get(c, 0) for c in name.upper() if c.isalpha()))

def fmt_dt(d): return d.strftime("%d-%b-%Y %H:%M")

def sign_name(s): return SIGNS[s % 12]

class _P:
    """Lightweight params holder (mirrors the old argparse namespace)."""
    def __init__(self, **kw):
        self.dob = kw.get("dob"); self.time = kw.get("time")
        self.place = kw.get("place"); self.state = kw.get("state")
        self.country = kw.get("country")
        self.lat = kw.get("lat"); self.lon = kw.get("lon"); self.tz = kw.get("tz")
        self.place_label = kw.get("place_label", "")
        self.name = kw.get("name"); self.out = kw.get("out")

def build_report(**kw):
    """Build the full kundali report and return it as a single string."""
    global L
    L = []
    a = _P(**kw)

    if a.lat is not None and a.lon is not None and a.tz:
        loc = {"name": a.place_label or f"{a.lat},{a.lon}", "country": "",
               "lat": a.lat, "lon": a.lon, "tz": a.tz}
    elif a.place:
        loc = geocode(a.place, a.state, a.country)
    else:
        raise ValueError("Provide place OR (lat, lon, tz)")

    ch = Chart(a.dob, a.time, loc["lat"], loc["lon"], loc["tz"],
               place_label=loc["name"], name=a.name)

    pan = ch.panchanga()
    # lords needed by kala bala: vara/hora/masa/abda
    ch.vara_lord = WEEKDAY_LORDS[pan["weekday"]]
    # hora lord: hours from sunrise, planetary hour sequence
    HORA_SEQ = ["Sun","Venus","Mercury","Moon","Saturn","Jupiter","Mars"]
    hrs = int((ch.jd - ch.jd_sunrise) * 24)
    ch.hora_lord = HORA_SEQ[(HORA_SEQ.index(ch.vara_lord) + hrs) % 7]
    # masa lord: lord of weekday 30 days after epoch start (approx: lord of the
    # weekday of the first day of the Hindu month) - simplified: weekday lord of
    # day (jd - tithi_elapsed_days)
    ch.masa_lord = ch.vara_lord
    ch.abda_lord = ch.vara_lord

    # ---------------- header
    hr("#"); w("VEDIC HOROSCOPE (KUNDALI) REPORT".center(78)); hr("#")
    w(f"Name        : {a.name or '-'}")
    w(f"Date of birth (local): {ch.local.strftime('%d %B %Y')}")
    w(f"Time of birth (local): {ch.local.strftime('%H:%M %Z')}")
    w(f"Place       : {loc['name']} {('('+loc['country']+')') if loc['country'] else ''}")
    w(f"Coordinates : {loc['lat']:.4f}N, {loc['lon']:.4f}E   Timezone: {loc['tz']}")
    w(f"Ayanamsa    : {ch.ayanamsa_name} = {dms(ch.ayanamsa, sign_rel=False)}")
    w(f"House system: Whole sign (Rashi = Bhava)")

    # ---------------- numerology
    sec("Numerology")
    d = ch.local
    mulank = digit_sum(d.day)
    bhagyank = digit_sum(sum(int(c) for c in d.strftime("%d%m%Y")))
    w(f"Mulank (Root/Driver number)  : {mulank}")
    w(f"Bhagyank (Destiny number)    : {bhagyank}")
    if a.name:
        w(f"Chaldean name number         : {name_number(a.name, CHALDEAN)}")
        w(f"Pythagorean name number      : {name_number(a.name, PYTHAGOREAN)}")
    else:
        w("Chaldean name number         : (name not supplied)")
        w("Pythagorean name number      : (name not supplied)")

    # ---------------- basic details
    sec("Basic Birth Details")
    asc_s = ch.asc_sign
    moon = ch.pos["Moon"]; moon_s = ch.sign_of(moon)
    nak, pada, _ = ch.nakshatra(moon)
    w(f"Lagna (Ascendant)   : {sign_name(asc_s)}  {dms(ch.asc)}")
    w(f"Lagna Lord          : {SIGN_LORDS[asc_s]}")
    w(f"Rashi (Moon sign)   : {sign_name(moon_s)}  {dms(moon)}")
    w(f"Rashi Lord          : {SIGN_LORDS[moon_s]}")
    w(f"Moon Nakshatra      : {NAKSHATRAS[nak]}")
    w(f"Nakshatra Pada      : {pada}")
    w(f"Nakshatra Lord      : {NAK_LORDS[nak]}")

    # ---------------- avakahada
    sec("Avakahada Chakra")
    # vashya edge cases (Sagittarius / Capricorn halves)
    vashya = VASHYA[moon_s]
    dgm = ch.deg_in_sign(moon)
    if moon_s == 8: vashya = "Manava" if dgm < 15 else "Chatushpada"
    if moon_s == 9: vashya = "Chatushpada" if dgm < 15 else "Jalachara"
    yoni_animal, yoni_g = YONI[nak]
    moon_house = ch.house_of(moon)
    paya = {1:"Swarna (Gold)",6:"Swarna (Gold)",11:"Swarna (Gold)",
            2:"Rajat (Silver)",5:"Rajat (Silver)",9:"Rajat (Silver)",
            3:"Tamra (Copper)",7:"Tamra (Copper)",10:"Tamra (Copper)",
            4:"Loha (Iron)",8:"Loha (Iron)",12:"Loha (Iron)"}[moon_house]
    w(f"Varna               : {VARNA[moon_s]}")
    w(f"Vashya              : {vashya}")
    w(f"Yoni                : {yoni_animal} ({'Male' if yoni_g=='M' else 'Female'})")
    w(f"Yoni lord (animal)  : {yoni_animal.split(' ')[0]}")
    w(f"Gana                : {GANA[nak]}")
    w(f"Gana category       : {GANA[nak]}")
    w(f"Nadi                : {NADI[nak]}")
    w(f"Nadi type           : {NADI[nak]}")
    w(f"Tithi               : {pan['tithi']} (#{pan['tithi_num']})")
    w(f"Paksha              : {pan['paksha']}")
    w(f"Yoga                : {pan['yoga']}")
    w(f"Karana              : {pan['karana']}")
    w(f"Weekday (Vedic)     : {pan['weekday']}")
    w(f"Paya (Moon in house {moon_house}) : {paya}")
    w(f"Tatva               : {TATVA[moon_s]}")
    w(f"Vedic name syllable : {SYLLABLES[nak][pada-1]}")

    # ---------------- D1 chart
    sec("Kundali — D1 Lagna Chart")
    for h in range(1, 13):
        s = (asc_s + h - 1) % 12
        lord = SIGN_LORDS[s]
        occ = [p for p in PLANETS9 if ch.sign_of(ch.pos[p]) == s]
        occ_str = ", ".join(f"{p} {dms(ch.pos[p])}" for p in occ) or "-"
        lord_house = ch.house_of(ch.pos[lord])
        w(f"House {h:2d} | {sign_name(s):<11} | Lord: {lord:<8}"
          f"(in H{lord_house:<2}) | {occ_str}")

    # ---------------- divisional charts
    sec("Divisional (Varga) Charts")
    ck = ch.chara_karakas()
    ak_planet = ck[0][1]
    d9 = ch.varga_chart(9)
    w(f"Karakamsha (AK={ak_planet} in D9) : {sign_name(d9['planet_signs'][ak_planet])}")
    w(f"Swamsa (D9 Lagna)          : {sign_name(d9['lagna_sign'])}")
    VARGAS = [(1,"Rashi"),(2,"Hora"),(3,"Drekkana"),(4,"Chaturthamsha"),
        (7,"Saptamsha"),(9,"Navamsha"),(10,"Dashamsha"),(12,"Dwadashamsha"),
        (16,"Shodashamsha"),(20,"Vimshamsha"),(24,"Chaturvimshamsha"),
        (27,"Saptavimshamsha"),(30,"Trimshamsha"),(40,"Khavedamsha"),
        (45,"Akshavedamsha"),(60,"Shashtiamsha")]
    for d, nm in VARGAS:
        vc = ch.varga_chart(d)
        w(); w(f"--- D{d} {nm} " + "-" * (78 - 10 - len(nm) - len(str(d))))
        w(f"Varga Lagna / Lagna sign : {sign_name(vc['lagna_sign'])} "
          f"(Lord: {SIGN_LORDS[vc['lagna_sign']]})")
        w("Planet positions:")
        for p in PLANETS9:
            w(f"  {p:<8}: {sign_name(vc['planet_signs'][p]):<11} (House {vc['planet_houses'][p]})")
        w("Houses:")
        for h in range(1, 13):
            occ = ", ".join(vc["houses"][h]) or "-"
            w(f"  H{h:2d} {sign_name(vc['house_signs'][h]):<11} "
              f"Lord: {vc['house_lords'][h]:<8} | {occ}")

    # ---------------- Vimshottari
    sec("Vimshottari Dasha")
    vd = vimshottari(ch)
    w(f"Balance at birth: {vd['balance_lord']} "
      f"{vd['balance_years']:.2f} years")
    w(); w("MAHADASHA -> ANTARDASHA -> PRATYANTARDASHA")
    for md in vd["mahadashas"]:
        w(f"\n{md['lord']} Mahadasha  {fmt_dt(md['start'])} to {fmt_dt(md['end'])}")
        for ad in md["antardashas"]:
            w(f"  └─ {ad['lord']:<8} AD {fmt_dt(ad['start'])} - {fmt_dt(ad['end'])}")
            for pd in ad["pratyantar"]:
                w(f"      └─ {pd['lord']:<8} PD "
                  f"{fmt_dt(pd['start'])} - {fmt_dt(pd['end'])}")
    cur = vd["current"]
    if cur:
        w(); w(f"CURRENT PERIOD (as of {fmt_dt(vd['as_of'])}):")
        w(f"  Mahadasha        : {cur['Mahadasha']['lord']}")
        w(f"  Antardasha       : {cur['Antardasha']['lord']}")
        w(f"  Pratyantardasha  : {cur['Pratyantardasha']['lord']}")
        w(f"  Sookshma         : {cur['Sookshma']['lord']} "
          f"({fmt_dt(cur['Sookshma']['start'])} - {fmt_dt(cur['Sookshma']['end'])})")
        w(f"  Prana            : {cur['Prana']['lord']} "
          f"({fmt_dt(cur['Prana']['start'])} - {fmt_dt(cur['Prana']['end'])})")

    # ---------------- Shadbala
    sec("Shadbala (virupas; 60 virupa = 1 rupa)")
    sb = shadbala(ch)
    hdr = f"{'Planet':<9}{'Sthana':>8}{'Dig':>7}{'Kala':>8}{'Cheshta':>8}" \
          f"{'Naisarg':>8}{'Drik':>7}{'Total':>8}{'Rupa':>7}{'Req':>6}" \
          f"{'Ratio':>7}{'Rank':>5}"
    w(hdr); w("-" * len(hdr))
    for p in PLANETS7:
        r = sb[p]
        chv = r["Cheshta"]["value"] if r["Cheshta"] else \
              ("(Ayana)" if p == "Sun" else "(Paksha)")
        chs = f"{chv:>8.1f}" if isinstance(chv, (int, float)) else f"{chv:>8}"
        w(f"{p:<9}{r['Sthana']['total']:>8.1f}{r['Dig']:>7.1f}"
          f"{r['Kala']['total']:>8.1f}{chs}"
          f"{r['Naisargika']:>8.1f}{r['Drik']:>7.1f}{r['total_virupa']:>8.1f}"
          f"{r['total_rupa']:>7.2f}{r['required_rupa']:>6.1f}"
          f"{r['ratio']:>7.2f}{r['rank']:>5}")
    w(); w("Sthana Bala components:")
    for p in PLANETS7:
        s = sb[p]["Sthana"]
        w(f"  {p:<8}: Uccha {s['Uccha']:.1f}, Saptavargaja {s['Saptavargaja']:.1f}, "
          f"Ojayugma {s['Ojayugma']:.1f}, Kendradi {s['Kendradi']:.1f}, "
          f"Drekkana {s['Drekkana']:.1f}")
    w(); w("Kala Bala components:")
    for p in PLANETS7:
        k = sb[p]["Kala"]
        w(f"  {p:<8}: Nathonnatha {k['Nathonnatha']:.1f}, Paksha {k['Paksha']:.1f}, "
          f"Tribhaga {k['Tribhaga']:.1f}, Abda {k['Abda']:.0f}, Masa {k['Masa']:.0f}, "
          f"Vara {k['Vara']:.0f}, Hora {k['Hora']:.0f}, Ayana {k['Ayana']:.1f}")
    w(); w("Cheshta (motion state):")
    for p in PLANETS7:
        c = sb[p]["Cheshta"]
        w(f"  {p:<8}: {c['motion'] if c else ('Ayana bala' if p=='Sun' else 'Paksha bala')}")

    # ---------------- Bhava Bala
    sec("Bhava Bala")
    bb = bhava_bala(ch, sb)
    w(f"{'House':<7}{'Lord':<9}{'Adhipati':>10}{'BhavaDig':>10}{'BhavaDrik':>11}"
      f"{'Total':>9}{'Rupa':>7}{'Rank':>6}")
    for h in range(1, 13):
        r = bb[h]
        w(f"{h:<7}{r['lord']:<9}{r['Bhavadhipati']:>10.1f}{r['BhavaDig']:>10.1f}"
          f"{r['BhavaDrik']:>11.1f}{r['total']:>9.1f}{r['rupa']:>7.2f}{r['rank']:>6}")

    # ---------------- Ashtakavarga
    sec("Ashtakavarga")
    bav, sav = ashtakavarga(ch)
    w("Bhinnashtakavarga (bindus per sign, Aries..Pisces):")
    w(f"{'Planet':<10}" + "".join(f"{s[:2]:>4}" for s in SIGNS) + f"{'Tot':>5}")
    for p in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        w(f"{p+' BAV':<10}" + "".join(f"{v:>4}" for v in bav[p]) +
          f"{sum(bav[p]):>5}")
    w(f"{'SAV':<10}" + "".join(f"{v:>4}" for v in sav) + f"{sum(sav):>5}")
    w(); w("Sarvashtakavarga by house (H1 = Lagna sign):")
    for h in range(1, 13):
        s = (asc_s + h - 1) % 12
        w(f"  House {h:2d} ({sign_name(s):<11}): {sav[s]} bindus")

    # ---------------- Aspects
    sec("Planet Drishti / Aspects")
    for p, info in ch.aspects().items():
        w(f"{p:<8} in House {info['from_house']:2d} aspects houses: "
          f"{', '.join(map(str, info['aspects_houses']))}")

    # ---------------- Chara Karakas
    sec("Chara Karakas (7-karaka scheme)")
    for kname, planet, deg in ck:
        w(f"{kname:<22}: {planet:<8} ({deg:.2f}° in sign)")

    # ---------------- Arudha padas
    sec("Arudha Padas")
    for hnum in range(1, 13):
        ap_sign = ch.arudha(hnum)
        label = {1: "AL  (Arudha Lagna)", 12: "UL  (Upapada Lagna)"}.get(
            hnum, f"A{hnum}")
        w(f"{label:<20}: {sign_name(ap_sign)} (House "
          f"{(ap_sign - asc_s) % 12 + 1})")

    # ---------------- Argala
    sec("Argala on Lagna")
    arg, vir = ch.argala(asc_s)
    for a2, planets in arg.items():
        v = vir[a2]
        w(f"Argala from {a2:2d}th : {', '.join(planets) or '-'}   | "
          f"Virodha ({({2:12,4:10,11:3}[a2])}th): {', '.join(v) or '-'}")

    # ---------------- Special Lagnas
    sec("Special Lagnas")
    sl = ch.special_lagnas()
    w(f"Ghatis elapsed since sunrise: {sl['ghatis_elapsed']:.2f}")
    for k in ("Bhava Lagna", "Hora Lagna", "Ghati Lagna", "Vighati Lagna"):
        v = sl[k]
        w(f"{k:<14}: {sign_name(int(v // 30))}  {dms(v)}")
    w(f"{'Indu Lagna':<14}: {sign_name(sl['Indu Lagna'])}")

    # ---------------- conventions
    sec("Conventions & Notes")
    for note in [
        "Ayanamsa: Lahiri (Chitrapaksha). Zodiac: sidereal. Houses: whole-sign.",
        "Ephemeris: Swiss Ephemeris (Moshier model, arc-second class accuracy).",
        "Rahu: true node; Ketu = Rahu + 180 deg.",
        "Chara Karakas: 7-karaka scheme (Sun..Saturn by degrees in sign).",
        "Vimshottari year = 365.2425 days. Full tree printed to Pratyantardasha;",
        "  Sookshma & Prana shown for the currently operating chain only.",
        "Cheshta Bala uses the Vakradi 8-fold motion classification.",
        "Kala Bala: Masa & Abda lords approximated by Vara lord (max impact",
        "  45 virupas); refine if cross-validating against other software.",
        "Shadbala/Bhava Bala conventions differ between softwares; expect small",
        "  numeric differences vs other tools, ranks are the robust output.",
        "Special Lagnas progress from sunrise Sun: BL 6 deg/ghati, HL 12,",
        "  GL 30; Vighati Lagna 30 deg/vighati. Indu Lagna via kala method.",
    ]:
        w(f"* {note}")

    w(); hr("#"); w("End of report".center(78)); hr("#")

    return "\n".join(L)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dob", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="HH:MM (24h, local)")
    ap.add_argument("--place", help="Town/City name")
    ap.add_argument("--state"); ap.add_argument("--country")
    ap.add_argument("--lat", type=float); ap.add_argument("--lon", type=float)
    ap.add_argument("--tz"); ap.add_argument("--place-label", default="")
    ap.add_argument("--name", help="Full name (for Chaldean/Pythagorean numbers)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    text = build_report(dob=a.dob, time=a.time, place=a.place, state=a.state,
                        country=a.country, lat=a.lat, lon=a.lon, tz=a.tz,
                        place_label=a.place_label, name=a.name)
    out = a.out or f"kundali_{a.dob}.txt"
    with open(out, "w") as f:
        f.write(text)
    print(f"Written: {out} ({len(text.splitlines())} lines)")

if __name__ == "__main__":
    main()
