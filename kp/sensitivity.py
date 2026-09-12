"""Birth-time precision.

Cusps sweep 133-180 arcminutes per 10 minutes of clock time, while sub spans
run 40-133 arcminutes wide. So over a wide window *every* cusp sub lord
changes -- measured at 12/12 across unrelated charts at +/-5 min. A binary
stable/unstable verdict over such a window carries no information.

What is informative is the margin: how accurate the recorded birth time must be
for a given cusp to hold. This module reports that per cusp, in minutes.

  holds_to_minutes   largest offset at which the sub lord still matches
  flips_at_minutes   smallest offset at which it differs (None if never)
  critical           holds for <= CRITICAL_MINUTES -- turns on the recorded minute
"""
from __future__ import annotations

from dataclasses import dataclass

from .chart import build_chart
from .context import BirthInput

DEFAULT_WINDOW_MIN = 2.0
DEFAULT_STEP_MIN = 0.5

# At or below this, the cusp depends on the exact recorded minute and anything
# derived from it should not be reported as settled.
CRITICAL_MINUTES = 1.0


@dataclass(frozen=True, slots=True)
class CuspStability:
    house: int
    base_sub_lord: str
    variants: tuple[str, ...]              # distinct sub lords seen, base first
    holds_to_minutes: float                # survives +/- this much
    flips_at_minutes: float | None         # first offset that differs
    window_minutes: float

    @property
    def holds_across_window(self) -> bool:
        return self.flips_at_minutes is None

    @property
    def critical(self) -> bool:
        return self.holds_to_minutes <= CRITICAL_MINUTES

    @property
    def precision_label(self) -> str:
        if self.holds_across_window:
            return f"\u00b1{self.window_minutes:g} min +"
        return f"\u00b1{self.holds_to_minutes:g} min"


@dataclass(frozen=True, slots=True)
class SensitivityReport:
    window_minutes: float
    step_minutes: float
    offsets: tuple[float, ...]
    per_offset: tuple[tuple[float, tuple[str, ...]], ...]
    cusps: tuple[CuspStability, ...]

    @property
    def critical_houses(self) -> tuple[int, ...]:
        return tuple(c.house for c in self.cusps if c.critical)

    @property
    def tightest_margin(self) -> float:
        return min(c.holds_to_minutes for c in self.cusps)

    @property
    def tightest_cusp(self) -> CuspStability:
        return min(self.cusps, key=lambda c: c.holds_to_minutes)

    def headline(self) -> str:
        crit = self.critical_houses
        if not crit:
            return (f"All twelve cusp sub lords hold to at least "
                    f"\u00b1{self.tightest_margin:g} min.")
        t = self.tightest_cusp
        flip = t.flips_at_minutes
        return (
            f"{len(crit)} of 12 cusps depend on the exact recorded minute: "
            f"house{'' if len(crit) == 1 else 's'} {', '.join(map(str, crit))}. "
            f"The tightest is house {t.house}, which changes sub lord within "
            f"\u00b1{flip:g} min. Confirm the birth time before relying on "
            "anything derived from these cusps."
        )


def scan(birth: BirthInput,
         window_minutes: float = DEFAULT_WINDOW_MIN,
         step_minutes: float = DEFAULT_STEP_MIN) -> SensitivityReport:
    if step_minutes <= 0:
        raise ValueError("step_minutes must be positive")
    if window_minutes < 0:
        raise ValueError("window_minutes must not be negative")

    n = int(round(window_minutes / step_minutes)) if window_minutes else 0
    offsets = tuple(round(i * step_minutes, 6) for i in range(-n, n + 1))

    rows = tuple(
        (off, tuple(c.sub_lord for c in
                    build_chart(birth if off == 0 else birth.shifted(off)).cusps))
        for off in offsets
    )
    by_offset = dict(rows)
    base = by_offset[0.0]

    radii = sorted({abs(o) for o in offsets})

    cusps: list[CuspStability] = []
    for h in range(12):
        seen = [base[h]]
        holds = 0.0
        flips: float | None = None
        for r in radii:
            ok = True
            for sign in (1, -1):
                probe = round(sign * r, 6)
                if probe not in by_offset:
                    continue
                val = by_offset[probe][h]
                if val != base[h]:
                    ok = False
                    if val not in seen:
                        seen.append(val)
                    if flips is None:
                        flips = r
            if ok and flips is None:
                holds = r
        cusps.append(CuspStability(
            house=h + 1,
            base_sub_lord=base[h],
            variants=tuple(seen),
            holds_to_minutes=holds,
            flips_at_minutes=flips,
            window_minutes=window_minutes,
        ))

    return SensitivityReport(
        window_minutes=window_minutes,
        step_minutes=step_minutes,
        offsets=offsets,
        per_offset=rows,
        cusps=tuple(cusps),
    )
