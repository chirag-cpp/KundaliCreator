"""Resolve any sidereal longitude into its KP lord chain.

Pure. No swisseph, no state -- so it is exhaustively unit-testable on its own.
"""
from __future__ import annotations

from dataclasses import dataclass

from .constants import (NAKSHATRAS, NAK_SPAN, PADA_SPAN, SIGN_LORD, SIGNS,
                        SUB_SPANS, sub_index, sub_sub_lord)


@dataclass(frozen=True, slots=True)
class LordChain:
    longitude: float
    sign: str
    sign_lord: str
    nakshatra: str
    pada: int
    star_lord: str
    sub_lord: str
    sub_sub_lord: str

    @property
    def dms(self) -> str:
        return format_dms(self.longitude)

    @property
    def display(self) -> str:
        return f"{self.dms} {self.sign}"


def format_dms(longitude: float) -> str:
    """Degrees within sign, as DD\u00b0MM'SS\"."""
    within = longitude % 30.0
    d = int(within)
    m_float = (within - d) * 60.0
    m = int(m_float)
    s = int(round((m_float - m) * 60.0))
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    return f"{d:02d}\u00b0{m:02d}'{s:02d}\""


def lords_of(longitude: float) -> LordChain:
    lon = longitude % 360.0
    span = SUB_SPANS[sub_index(lon)]
    si = int(lon // 30.0)
    ni = int(lon // NAK_SPAN)
    pada = int((lon % NAK_SPAN) // PADA_SPAN) + 1
    return LordChain(
        longitude=lon,
        sign=SIGNS[si],
        sign_lord=SIGN_LORD[si],
        nakshatra=NAKSHATRAS[ni],
        pada=pada,
        star_lord=span.star_lord,
        sub_lord=span.sub_lord,
        sub_sub_lord=sub_sub_lord(lon, span),
    )
