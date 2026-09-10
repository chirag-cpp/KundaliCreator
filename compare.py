# -*- coding: utf-8 -*-
"""
compare.py — diagnose a profile that disagrees with another astrology app.
Everything runs locally; nothing is sent anywhere.

  python3 compare.py --dob 1991-09-16 --time 22:50 --place "Naya Nangal" --country IN
  python3 compare.py --dob ... --time ... --lat 31.39 --lon 76.38 --tz Asia/Kolkata

Optionally paste the other app's 12 SAV totals to get a direct diff:
  ... --sav 24,38,38,28,24,21,34,22,24,26,26,32
"""
import argparse
import swisseph as swe
from core import Chart, geocode_candidates, _lahiri
from strength import ashtakavarga
from tables import SIGNS, SIGN_LORDS, PLANETS7, NAKSHATRAS, NAK_LORDS

AY = {"Lahiri": swe.SIDM_LAHIRI, "True Chitra": swe.SIDM_TRUE_CITRA,
      "Krishnamurti": swe.SIDM_KRISHNAMURTI, "Raman": swe.SIDM_RAMAN,
      "Fagan-Bradley (library default)": swe.SIDM_FAGAN_BRADLEY}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dob", required=True); p.add_argument("--time", required=True)
    p.add_argument("--place"); p.add_argument("--country")
    p.add_argument("--lat", type=float); p.add_argument("--lon", type=float)
    p.add_argument("--tz"); p.add_argument("--sav")
    a = p.parse_args()

    if a.lat is not None and a.lon is not None and a.tz:
        lat, lon, tz, label = a.lat, a.lon, a.tz, "(coordinates)"
    else:
        cands = geocode_candidates(a.place, a.country, limit=5)
        if not cands:
            print("No place match. Use --lat --lon --tz."); return
        c = cands[0]
        lat, lon, tz = c["lat"], c["lon"], c["tz"]
        label = f"{c['name']} ({c['country']})"
        if len(cands) > 1:
            print("NOTE: place was ambiguous. Using the first; others were:")
            for o in cands[1:]:
                print(f"   {o['name']} ({o['country']}) {o['lat']:.2f},{o['lon']:.2f}")
            print("   A wrong town shifts the Lagna. Verify this is right.\n")

    ch = Chart(a.dob, a.time, lat, lon, tz)
    print("=" * 66)
    print(f"{a.dob} {a.time}  {label}  {lat:.4f},{lon:.4f}  {tz}")
    print("=" * 66)

    # 1. is the sidereal mode actually Lahiri?
    print("\n[1] SIDEREAL MODE")
    print(f"    ayanamsa in use : {ch.ayanamsa_name} = {ch.ayanamsa:.6f} deg")
    print("    (if this does not say Lahiri, the guard failed — report it)")

    # 2. placements and how close each is to a sign boundary
    print("\n[2] PLACEMENTS AND BOUNDARY RISK")
    print("    A planet within ~1 deg of a sign edge can legitimately differ")
    print("    between tools using different ayanamsas or birth-time rounding.")
    risky = []
    for pl in PLANETS7 + ["Rahu", "Ketu"]:
        d = ch.deg_in_sign(ch.pos[pl])
        edge = min(d, 30 - d)
        flag = ""
        if edge < 1.0:
            flag = "  <== AT RISK"; risky.append(pl)
        print(f"    {pl:8s} {SIGNS[ch.sign_of(ch.pos[pl])]:<12} {d:6.2f} deg"
              f"   nearest edge {edge:5.2f} deg{flag}")
    d = ch.deg_in_sign(ch.asc); edge = min(d, 30 - d)
    flag = "  <== AT RISK" if edge < 1.0 else ""
    print(f"    {'Lagna':8s} {SIGNS[ch.asc_sign]:<12} {d:6.2f} deg"
          f"   nearest edge {edge:5.2f} deg{flag}")
    if risky:
        print(f"\n    {len(risky)} body/bodies near an edge: {', '.join(risky)}")
        print("    THIS is the usual cause of a profile disagreeing.")

    # 3. what other ayanamsas would give
    print("\n[3] WOULD ANOTHER AYANAMSA CHANGE THE SIGNS?")
    base = {pl: ch.sign_of(ch.pos[pl]) for pl in PLANETS7}
    for nm, mode in AY.items():
        swe.set_sid_mode(mode)
        ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
               "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
               "Venus": swe.VENUS, "Saturn": swe.SATURN}
        F = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        diff = [pl for pl, i in ids.items()
                if int(swe.calc_ut(ch.jd, i, F)[0][0] % 360 // 30) != base[pl]]
        asc2 = int(swe.houses_ex(ch.jd, lat, lon, b'W',
                                 swe.FLG_SIDEREAL)[1][0] % 360 // 30)
        if asc2 != ch.asc_sign:
            diff.append("Lagna")
        print(f"    {nm:34s} {'same signs' if not diff else 'DIFFERS: ' + ', '.join(diff)}")
    _lahiri()

    # 4. Ashtakavarga in the layout other apps use
    bav, sav = ashtakavarga(ch)
    print("\n[4] ASHTAKAVARGA — 'RN' LAYOUT (RN = Rashi number, Aries = 1)")
    print("    RN Sign          Su Mo Ma Me Ju Ve Sa  Tot  House")
    for s in range(12):
        h = (s - ch.asc_sign) % 12 + 1
        row = "".join(f"{bav[p][s]:>3}" for p in
                      ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"])
        print(f"    {s+1:2d} {SIGNS[s]:<12}{row}  {sav[s]:>3}   H{h}")
    print(f"    total = {sum(sav)} (must be 337)")

    if a.sav:
        ref = [int(x) for x in a.sav.replace(" ", "").split(",")]
        print("\n[5] DIFF AGAINST THE VALUES YOU PASTED")
        if len(ref) != 12:
            print("    need exactly 12 comma-separated numbers")
        elif sum(ref) != 337:
            print(f"    their total is {sum(ref)}, not 337 — they applied a")
            print("    reduction (Trikona/Ekadhipatya). Different convention,")
            print("    not an error on either side.")
        else:
            bad = [i for i in range(12) if sav[i] != ref[i]]
            if not bad:
                print("    IDENTICAL — no discrepancy.")
            else:
                rot = next((r for r in range(1, 12)
                            if all(sav[(i + r) % 12] == ref[i] for i in range(12))),
                           None)
                if rot is not None:
                    print(f"    Same numbers, rotated by {rot}. Their row 1 is not")
                    print("    Aries — it is a house-indexed grid. Not a bug.")
                else:
                    print("    Genuine mismatch at RN " +
                          ", ".join(str(i + 1) for i in bad))
                    for i in bad:
                        print(f"      RN {i+1:2d} {SIGNS[i]:<12} mine {sav[i]:>3} "
                              f"theirs {ref[i]:>3}")
                    print("    Cross-check the placements in [2] against their")
                    print("    chart — one planet is in a different sign.")

if __name__ == "__main__":
    main()
