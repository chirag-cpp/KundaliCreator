"""Assemble the immutable KPChart. Owns house allocation by cusp."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .constants import PLANET_ORDER, SIGN_LORD
from .context import BirthInput
from .ephemeris import ayanamsa_value, placidus_cusps, planet_longitudes
from .lords import LordChain, lords_of


@dataclass(frozen=True, slots=True)
class PlanetPosition:
    name: str
    chain: LordChain
    house: int
    retrograde: bool


@dataclass(frozen=True, slots=True)
class KPChart:
    birth: BirthInput
    ayanamsa_deg: float
    cusps: tuple[LordChain, ...]                  # index 0 == house 1
    planets: Mapping[str, PlanetPosition]
    ascendant: float

    # ---- derived views (computed, never stored mutable) ----
    def occupants(self) -> dict[int, list[str]]:
        out: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        for name in PLANET_ORDER:
            out[self.planets[name].house].append(name)
        return out

    def ownerships(self) -> dict[str, list[int]]:
        """Houses owned = houses whose cusp falls in a sign ruled by that planet.
        Nodes own nothing."""
        out: dict[str, list[int]] = {}
        for i, chain in enumerate(self.cusps):
            out.setdefault(chain.sign_lord, []).append(i + 1)
        return out

    def cuspal_sub_lord(self, house: int) -> str:
        return self.cusps[house - 1].sub_lord

    def house_of(self, longitude: float) -> int:
        return house_of(tuple(c.longitude for c in self.cusps), longitude)


def house_of(cusps: tuple[float, ...], longitude: float) -> int:
    """Which house a longitude falls in, given 12 Placidus cusps.

    Handles the 0/360 wrap: exactly one of the twelve arcs crosses it.
    Half-open [cusp_n, cusp_n+1).
    """
    lon = longitude % 360.0
    for i in range(12):
        a = cusps[i] % 360.0
        b = cusps[(i + 1) % 12] % 360.0
        if a <= b:
            if a <= lon < b:
                return i + 1
        else:                                     # this arc spans 0 deg
            if lon >= a or lon < b:
                return i + 1
    raise ValueError(f"longitude {longitude} matched no house arc")


def build_chart(birth: BirthInput) -> KPChart:
    cusp_lons, ascmc = placidus_cusps(birth)
    cusp_chains = tuple(lords_of(c) for c in cusp_lons)

    raw = planet_longitudes(birth)
    planets: dict[str, PlanetPosition] = {}
    for name in PLANET_ORDER:
        lon, retro = raw[name]
        planets[name] = PlanetPosition(
            name=name,
            chain=lords_of(lon),
            house=house_of(cusp_lons, lon),
            retrograde=retro,
        )

    return KPChart(
        birth=birth,
        ayanamsa_deg=ayanamsa_value(birth),
        cusps=cusp_chains,
        planets=MappingProxyType(planets),        # read-only view
        ascendant=ascmc[0] % 360.0,
    )
