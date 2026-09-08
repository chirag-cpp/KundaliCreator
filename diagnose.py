"""Run this in the SAME environment where you saw 24 deg 29' 22\"."""
import swisseph as swe
print("pyswisseph version:", swe.version)
jd82 = swe.julday(1982, 1, 13, 12)
print("\nBEFORE setting mode (library default):")
print("  1982 ayanamsa:", round(swe.get_ayanamsa_ut(jd82), 6))
swe.set_sid_mode(swe.SIDM_LAHIRI)
print("\nAFTER set_sid_mode(SIDM_LAHIRI):")
print("  mode constant SIDM_LAHIRI =", swe.SIDM_LAHIRI)
print("  name reported            :", swe.get_ayanamsa_name(swe.SIDM_LAHIRI))
a = swe.get_ayanamsa_ut(jd82)
d = int(a); m = int((a - d) * 60); s = ((a - d) * 60 - m) * 60
print(f"  1982 ayanamsa            : {a:.6f} = {d}d {m:02d}' {s:04.1f}\"")
print("\nEXPECTED : 23.606140 = 23d 36' 22.1\"  (Lahiri)")
print("IF YOU SEE: 24.489361 = 24d 29' 21.7\"  -> library is on Fagan-Bradley")
print("\nThrough the engine:")
try:
    from generate_kundali import build_report
    r = build_report(dob='1982-01-13', time='14:30', place='Ghaziabad', country='IN')
    print(" ", [l for l in r.splitlines() if l.startswith('Ayanamsa')][0])
except Exception as e:
    print("  engine error:", e)
