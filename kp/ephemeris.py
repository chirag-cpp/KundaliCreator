"""The only module in the package that talks to swisseph.

Every entry point wraps its calls in ``sidereal_mode`` so the global sid mode is
restored even on error.
"""
from __future__ import annotations

import swisseph as swe

from .context import BirthInput, PolarLatitudeError, sidereal_mode

_BODIES: tuple[tuple[str, int], ...] = (
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
)

_CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

# NODE CONVENTION -- a deliberate divergence from the Lahiri engine.
#
#   core.py (Parashari)  uses swe.TRUE_NODE
#   this module (KP)     uses swe.MEAN_NODE
#
# KP practice is the Mean node, so this is correct for KP rather than an
# oversight -- but it means Rahu/Ketu sit a few arcminutes apart between the
# two tabs, which can move a sub lord. The KP tab states this in its caption.
# Set to swe.TRUE_NODE here if you would rather the two tabs agree; regenerate
# the golden fixture afterwards.
_NODE = swe.MEAN_NODE


def ayanamsa_value(birth: BirthInput) -> float:
    with sidereal_mode(birth.ayanamsa):
        return swe.get_ayanamsa_ut(birth.julian_day_ut)


def planet_longitudes(birth: BirthInput) -> dict[str, tuple[float, bool]]:
    """{name: (sidereal_longitude, is_retrograde)}.

    Nodes are always retrograde by construction; that is expected, not an
    anomaly, and callers should not flag it.
    """
    jd = birth.julian_day_ut
    out: dict[str, tuple[float, bool]] = {}
    with sidereal_mode(birth.ayanamsa):
        for name, pid in _BODIES:
            xx, _ = swe.calc_ut(jd, pid, _CALC_FLAGS)
            out[name] = (xx[0] % 360.0, xx[3] < 0)
        xx, _ = swe.calc_ut(jd, _NODE, _CALC_FLAGS)
        out["Rahu"] = (xx[0] % 360.0, True)
        out["Ketu"] = ((xx[0] + 180.0) % 360.0, True)
    return out


def placidus_cusps(birth: BirthInput) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """(12 cusps, ascmc) in sidereal longitudes under the KP ayanamsa.

    Computed *in* the KP ayanamsa -- never by shifting a Lahiri chart, which
    would move every cusp sub lord with no visible error.
    """
    with sidereal_mode(birth.ayanamsa):
        try:
            cusps, ascmc = swe.houses_ex(
                birth.julian_day_ut, birth.latitude, birth.longitude,
                b"P", swe.FLG_SIDEREAL,
            )
        except swe.Error as exc:                      # pragma: no cover
            raise PolarLatitudeError(
                f"Placidus cusps unavailable at latitude {birth.latitude}: {exc}"
            ) from exc
    cusps = tuple(c % 360.0 for c in cusps[:12])
    if len(cusps) != 12 or any(c != c for c in cusps):   # NaN guard
        raise PolarLatitudeError(
            f"Placidus returned an invalid cusp set at latitude {birth.latitude}"
        )
    return cusps, tuple(ascmc)


def previous_sunrise_jd(birth: BirthInput) -> float | None:
    """JD(UT) of the last sunrise at or before the birth moment.

    KP's day lord changes at local sunrise, not midnight. Returns None if the
    sun is circumpolar (no rise event), which callers must handle rather than
    silently falling back to a calendar weekday.
    """
    jd = birth.julian_day_ut
    with sidereal_mode(birth.ayanamsa):
        for back in (1.0, 2.0):
            try:
                res, tret = swe.rise_trans(
                    jd - back, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER,
                    birth.geopos, 0.0, 0.0, swe.FLG_SWIEPH,
                )
            except swe.Error:                          # pragma: no cover
                return None
            if res != 0:
                return None
            # rise_trans returns the *next* rise after the given jd; walk
            # forward until we pass the birth moment, then step back one.
            last = None
            probe = jd - back
            for _ in range(4):
                res, tret = swe.rise_trans(
                    probe, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER,
                    birth.geopos, 0.0, 0.0, swe.FLG_SWIEPH,
                )
                if res != 0:
                    break
                if tret[0] > jd:
                    break
                last = tret[0]
                probe = tret[0] + 0.01
            if last is not None:
                return last
    return None
