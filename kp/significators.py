"""Significator derivation.

Two related outputs:

1. ``house_significators`` -- the classic four-level grid, per house:
     A  planets tenanting the star of an occupant of that house
     B  occupants of that house
     C  planets tenanting the star of the owner of that house
     D  owner of that house

2. ``planet_significations`` -- the inverse view, per planet:
     primary   = houses occupied and owned by its STAR lord
     secondary = houses occupied and owned by ITSELF
   This is the view used for cuspal-sub-lord verdicts.

Node agency: Rahu/Ketu own no sign. They act for (a) their star lord, and
(b) the lord of the sign they occupy. Conjunction agency is deliberately
omitted -- it needs an orb convention, and orb choice is an interpretive
decision this package does not make.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .chart import KPChart
from .constants import NODES, PLANET_ORDER


@dataclass(frozen=True, slots=True)
class HouseSignificators:
    house: int
    level_a: tuple[str, ...]      # in star of occupant
    level_b: tuple[str, ...]      # occupant
    level_c: tuple[str, ...]      # in star of owner
    level_d: tuple[str, ...]      # owner

    def all_planets(self) -> tuple[str, ...]:
        seen: list[str] = []
        for grp in (self.level_a, self.level_b, self.level_c, self.level_d):
            for p in grp:
                if p not in seen:
                    seen.append(p)
        return tuple(seen)


@dataclass(frozen=True, slots=True)
class PlanetSignification:
    planet: str
    star_lord: str
    primary: tuple[int, ...]      # via star lord
    secondary: tuple[int, ...]    # own occupation + ownership
    in_own_star: bool
    no_planets_in_its_star: bool

    @property
    def positional_status(self) -> bool:
        """KP 'positional status': a planet in its own star, or with no planet
        tenanting its star, acts as a primary significator in its own right."""
        return self.in_own_star or self.no_planets_in_its_star

    def all_houses(self) -> tuple[int, ...]:
        return tuple(sorted(set(self.primary) | set(self.secondary)))

    def signifies(self, houses: set[int]) -> set[int]:
        return houses & set(self.all_houses())


def _sorted_unique(seq) -> tuple:
    out: list = []
    for x in seq:
        if x not in out:
            out.append(x)
    return tuple(out)


def house_significators(chart: KPChart) -> tuple[HouseSignificators, ...]:
    occ = chart.occupants()
    own = chart.ownerships()

    result: list[HouseSignificators] = []
    for h in range(1, 13):
        occupants = occ.get(h, [])
        owners = [p for p in PLANET_ORDER if h in own.get(p, [])]
        level_a = [p for p in PLANET_ORDER
                   if chart.planets[p].chain.star_lord in occupants]
        level_c = [p for p in PLANET_ORDER
                   if chart.planets[p].chain.star_lord in owners]
        result.append(HouseSignificators(
            house=h,
            level_a=tuple(level_a),
            level_b=tuple(occupants),
            level_c=tuple(level_c),
            level_d=tuple(owners),
        ))
    return tuple(result)


def _houses_of_agent(chart: KPChart, agent: str,
                     own: dict[str, list[int]]) -> list[int]:
    """Houses a planet stands for: the one it occupies plus the ones it owns."""
    return [chart.planets[agent].house] + list(own.get(agent, []))


def planet_significations(chart: KPChart) -> dict[str, PlanetSignification]:
    own = chart.ownerships()
    star_of = {p: chart.planets[p].chain.star_lord for p in PLANET_ORDER}
    tenants_of_star: dict[str, list[str]] = {}
    for p in PLANET_ORDER:
        tenants_of_star.setdefault(star_of[p], []).append(p)

    out: dict[str, PlanetSignification] = {}
    for p in PLANET_ORDER:
        star = star_of[p]
        primary = _houses_of_agent(chart, star, own)
        secondary = _houses_of_agent(chart, p, own)

        # Node agency: add the sign lord of the sign the node occupies.
        if p in NODES:
            sign_lord = chart.planets[p].chain.sign_lord
            if sign_lord != p:
                primary += _houses_of_agent(chart, sign_lord, own)
        if star in NODES:
            node_sign_lord = chart.planets[star].chain.sign_lord
            if node_sign_lord != star:
                primary += _houses_of_agent(chart, node_sign_lord, own)

        out[p] = PlanetSignification(
            planet=p,
            star_lord=star,
            primary=_sorted_unique(primary),
            secondary=_sorted_unique(secondary),
            in_own_star=(star == p),
            no_planets_in_its_star=(p not in tenants_of_star),
        )
    return out


# --- Matter -> required house group. Structural only; no verdict text. ---
HOUSE_GROUPS: dict[str, tuple[int, ...]] = {
    "Marriage": (2, 7, 11),
    "Career (service)": (2, 6, 10),
    "Career (independent)": (2, 7, 11),
    "Wealth": (2, 6, 10, 11),
    "Children": (2, 5, 11),
    "Education": (4, 9, 11),
    "Property": (4, 11, 12),
    "Foreign residence": (3, 9, 12),
    "Health/vitality": (1, 5, 9, 11),
}

# Which cusp is consulted for each matter.
MATTER_CUSP: dict[str, int] = {
    "Marriage": 7, "Career (service)": 10, "Career (independent)": 10,
    "Wealth": 2, "Children": 5, "Education": 4, "Property": 4,
    "Foreign residence": 12, "Health/vitality": 1,
}


@dataclass(frozen=True, slots=True)
class CuspalCheck:
    matter: str
    cusp: int
    sub_lord: str
    required: tuple[int, ...]
    matched: tuple[int, ...]
    missing: tuple[int, ...]


def cuspal_checks(chart: KPChart) -> tuple[CuspalCheck, ...]:
    """Mechanical set intersection between what a CSL signifies and what a
    matter requires. Reports matched/missing houses only -- it does not decide
    whether that constitutes a promise."""
    sig = planet_significations(chart)
    out: list[CuspalCheck] = []
    for matter, required in HOUSE_GROUPS.items():
        cusp = MATTER_CUSP[matter]
        csl = chart.cuspal_sub_lord(cusp)
        have = set(sig[csl].all_houses())
        out.append(CuspalCheck(
            matter=matter,
            cusp=cusp,
            sub_lord=csl,
            required=required,
            matched=tuple(h for h in required if h in have),
            missing=tuple(h for h in required if h not in have),
        ))
    return tuple(out)
