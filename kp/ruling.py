"""Ruling Planets.

The day lord changes at local SUNRISE, not midnight. A birth between midnight
and sunrise belongs to the previous weekday. If sunrise cannot be determined,
``day_lord`` is None and the caller must say so rather than substituting the
calendar weekday.
"""
from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from .chart import KPChart
from .ephemeris import previous_sunrise_jd
from .lords import lords_of

# Python weekday(): Monday == 0
WEEKDAY_LORD: tuple[str, ...] = (
    "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun",
)


@dataclass(frozen=True, slots=True)
class RulingPlanets:
    lagna_sign_lord: str
    lagna_star_lord: str
    lagna_sub_lord: str
    moon_sign_lord: str
    moon_star_lord: str
    moon_sub_lord: str
    day_lord: str | None
    sunrise_resolved: bool

    def ordered(self) -> tuple[str, ...]:
        """Descending strength: lagna sub, lagna star, lagna sign,
        moon sub, moon star, moon sign, day lord. Deduplicated."""
        seq = [self.lagna_sub_lord, self.lagna_star_lord, self.lagna_sign_lord,
               self.moon_sub_lord, self.moon_star_lord, self.moon_sign_lord]
        if self.day_lord:
            seq.append(self.day_lord)
        out: list[str] = []
        for p in seq:
            if p not in out:
                out.append(p)
        return tuple(out)


def _weekday_from_sunrise(jd_sunrise: float, tz_offset_hours: float) -> str:
    y, m, d, _ = swe.revjul(jd_sunrise + tz_offset_hours / 24.0)
    import datetime as _dt
    return WEEKDAY_LORD[_dt.date(y, m, d).weekday()]


def ruling_planets(chart: KPChart) -> RulingPlanets:
    lagna = lords_of(chart.ascendant)
    moon = chart.planets["Moon"].chain

    jd_rise = previous_sunrise_jd(chart.birth)
    if jd_rise is None:
        day_lord, resolved = None, False
    else:
        day_lord = _weekday_from_sunrise(jd_rise, chart.birth.tz_offset_hours)
        resolved = True

    return RulingPlanets(
        lagna_sign_lord=lagna.sign_lord,
        lagna_star_lord=lagna.star_lord,
        lagna_sub_lord=lagna.sub_lord,
        moon_sign_lord=moon.sign_lord,
        moon_star_lord=moon.star_lord,
        moon_sub_lord=moon.sub_lord,
        day_lord=day_lord,
        sunrise_resolved=resolved,
    )
