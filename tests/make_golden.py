"""Regenerate the golden fixture. Run ONLY after re-validating against the
third-party reference app, and commit the diff deliberately."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from kp import (BirthInput, KPAyanamsa, build_chart, house_significators,
                planet_significations, ruling_planets)

NANGAL = BirthInput(
    year=1991, month=9, day=16, hour=22, minute=50,
    tz_offset_hours=5.5, latitude=31.3880, longitude=76.3773,
    ayanamsa=KPAyanamsa.CLASSIC,
)


def snapshot(birth: BirthInput) -> dict:
    ch = build_chart(birth)
    sig = planet_significations(ch)
    rp = ruling_planets(ch)
    return {
        "ayanamsa_deg": round(ch.ayanamsa_deg, 9),
        "ascendant": round(ch.ascendant, 9),
        "cusps": [
            {"house": i + 1, "lon": round(c.longitude, 9), "sign": c.sign,
             "nakshatra": c.nakshatra, "pada": c.pada, "star": c.star_lord,
             "sub": c.sub_lord, "subsub": c.sub_sub_lord}
            for i, c in enumerate(ch.cusps)
        ],
        "planets": [
            {"name": p.name, "lon": round(p.chain.longitude, 9),
             "sign": p.chain.sign, "house": p.house,
             "nakshatra": p.chain.nakshatra, "pada": p.chain.pada,
             "star": p.chain.star_lord, "sub": p.chain.sub_lord,
             "subsub": p.chain.sub_sub_lord, "retro": p.retrograde}
            for p in (ch.planets[n] for n in
                      ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                       "Venus", "Saturn", "Rahu", "Ketu"])
        ],
        "ownerships": {k: v for k, v in sorted(ch.ownerships().items())},
        "significators": [
            {"house": h.house, "A": list(h.level_a), "B": list(h.level_b),
             "C": list(h.level_c), "D": list(h.level_d)}
            for h in house_significators(ch)
        ],
        "planet_significations": {
            p: {"star": s.star_lord, "primary": list(s.primary),
                "secondary": list(s.secondary),
                "positional_status": s.positional_status}
            for p, s in sorted(sig.items())
        },
        "ruling_planets": {"ordered": list(rp.ordered()),
                           "day_lord": rp.day_lord,
                           "sunrise_resolved": rp.sunrise_resolved},
    }


if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "golden" / "kp_nangal_19910916.json"
    out.write_text(json.dumps(snapshot(NANGAL), indent=2, sort_keys=True))
    print(f"wrote {out}")
