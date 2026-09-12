"""Static KP tables. Pure data + pure functions. No swisseph, no I/O, no globals
that anything outside this package can mutate.
"""
from __future__ import annotations

from bisect import bisect_right
from typing import NamedTuple

# --- Vimshottari (the ordering is load-bearing: sub sequence follows it) ---
VIMSHOTTARI: tuple[tuple[str, int], ...] = (
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
)
LORDS: tuple[str, ...] = tuple(p for p, _ in VIMSHOTTARI)
YEARS: dict[str, int] = {p: y for p, y in VIMSHOTTARI}
TOTAL_YEARS = 120
assert sum(YEARS.values()) == TOTAL_YEARS

NAKSHATRAS: tuple[str, ...] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "P.Phalguni", "U.Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "P.Ashadha", "U.Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "P.Bhadrapada", "U.Bhadrapada", "Revati",
)
NAKSHATRA_LORD: tuple[str, ...] = tuple(LORDS[i % 9] for i in range(27))

SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGN_LORD: tuple[str, ...] = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
)

NAK_SPAN = 360.0 / 27.0          # 13.3333... deg
PADA_SPAN = NAK_SPAN / 4.0

# Rahu/Ketu own no sign. They act as agents (see significators.py).
NODES = ("Rahu", "Ketu")
PLANET_ORDER: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


class SubSpan(NamedTuple):
    start: float          # inclusive
    end: float            # exclusive
    nakshatra_index: int
    star_lord: str
    sub_lord: str


def _build_subs() -> tuple[SubSpan, ...]:
    """243 star/sub spans covering 0-360 deg.

    Note: the familiar '249' figure counts sub spans *split at sign boundaries*
    (used for horary 1-249). For longitude lookup 243 contiguous spans are the
    correct and complete partition; the sign is derived from the longitude
    itself, so no split is needed here.
    """
    spans: list[SubSpan] = []
    for n in range(27):
        star = NAKSHATRA_LORD[n]
        i0 = LORDS.index(star)
        pos = n * NAK_SPAN
        for k in range(9):
            p = LORDS[(i0 + k) % 9]
            width = NAK_SPAN * YEARS[p] / TOTAL_YEARS
            end = pos + width
            if n == 26 and k == 8:
                end = 360.0          # kill float drift at the wrap point
            spans.append(SubSpan(pos, end, n, star, p))
            pos = end
    return tuple(spans)


SUB_SPANS: tuple[SubSpan, ...] = _build_subs()
_SUB_STARTS: tuple[float, ...] = tuple(s.start for s in SUB_SPANS)

assert len(SUB_SPANS) == 243
assert abs(SUB_SPANS[-1].end - 360.0) < 1e-9


def sub_index(longitude: float) -> int:
    """O(log n) lookup. Spans are half-open [start, end)."""
    lon = longitude % 360.0
    return bisect_right(_SUB_STARTS, lon) - 1


def sub_sub_lord(longitude: float, span: SubSpan) -> str:
    """Fourth level: subdivide the sub span by the same proportions,
    starting from the sub lord."""
    lon = longitude % 360.0
    i0 = LORDS.index(span.sub_lord)
    total = span.end - span.start
    pos = span.start
    for k in range(9):
        p = LORDS[(i0 + k) % 9]
        pos += total * YEARS[p] / TOTAL_YEARS
        if lon < pos:
            return p
    return LORDS[(i0 + 8) % 9]       # boundary fallthrough
