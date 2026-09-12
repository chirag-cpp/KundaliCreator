"""Isolation layer.

The single most dangerous thing about adding KP to an existing Lahiri engine is
that ``swe.set_sid_mode()`` mutates *process-global* state inside the C library.
If KP sets Krishnamurti and does not restore it, every later Lahiri calculation
in the same run returns wrong values silently -- no exception, no warning.

Everything in this package goes through ``sidereal_mode``. The existing engine
should be retrofitted to do the same.
"""
from __future__ import annotations

import datetime as _dt
from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum

import swisseph as swe

# --- sidereal mode tracking -------------------------------------------------
# Swiss Ephemeris exposes set_sid_mode() but NO getter: the current mode is
# write-only. So we cannot ask the library what it is set to, and a hardcoded
# "restore to X" constant is an unverifiable assumption. Instead this module
# owns the state -- every set goes through set_mode(), so _current_mode is
# always true, and the guard restores whatever was actually in effect rather
# than a named default.
DEFAULT_SID_MODE = swe.SIDM_LAHIRI

# NOTE: importing this module must not touch swisseph. The host application
# may already have set its own mode before importing kp; writing here would
# silently clobber it. So we only record the *assumed* mode and leave the
# library alone until something actually asks for a calculation.
#
# Call configure_default() once at startup so this assumption is true.
_current_mode: int = int(DEFAULT_SID_MODE)


def set_mode(sid_mode: int) -> None:
    """The only sanctioned way to change the sidereal mode. Call this instead
    of swe.set_sid_mode() anywhere in the application."""
    global _current_mode
    swe.set_sid_mode(int(sid_mode))
    _current_mode = int(sid_mode)


def current_mode() -> int:
    """The mode this module believes is in effect. Accurate as long as nothing
    bypasses set_mode()/sidereal_mode()."""
    return _current_mode


def configure_default(sid_mode: int) -> None:
    """Call once at application startup with whatever ayanamsa the rest of the
    engine assumes. Replaces the module default."""
    global DEFAULT_SID_MODE
    DEFAULT_SID_MODE = int(sid_mode)
    set_mode(sid_mode)

# Placidus is undefined inside the polar circles; swisseph will return values
# anyway rather than failing, so we gate it ourselves.
POLAR_LIMIT_DEG = 66.0


class KPAyanamsa(IntEnum):
    """The two Krishnamurti ayanamsas shipped with Swiss Ephemeris.

    They differ by roughly one arc-minute -- enough to change a sub lord.
    Whichever you validate against, record it with the chart.
    """
    CLASSIC = int(swe.SIDM_KRISHNAMURTI)
    VP291 = 45          # SE_SIDM_KRISHNAMURTI_VP291 (2019 reconstruction)


class PolarLatitudeError(ValueError):
    """Placidus cusps are not defined at this latitude."""


@contextmanager
def sidereal_mode(sid_mode: int):
    """Set the sidereal mode for the duration of the block, then restore the
    mode that was previously in effect.

    Restoration happens in ``finally``, so an exception inside the block cannot
    leave the library in the wrong mode. Nesting is safe: each block restores
    its own predecessor, not a global default.
    """
    previous = _current_mode
    set_mode(sid_mode)
    try:
        yield
    finally:
        set_mode(previous)


@dataclass(frozen=True, slots=True)
class BirthInput:
    """Immutable. Nothing downstream may modify it; attempts raise."""
    year: int
    month: int
    day: int
    hour: int
    minute: int
    tz_offset_hours: float          # local time = UT + offset
    latitude: float
    longitude: float                # east positive
    altitude_m: float = 0.0
    ayanamsa: KPAyanamsa = KPAyanamsa.CLASSIC
    second: int = 0

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(f"latitude out of range: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(f"longitude out of range: {self.longitude}")
        if abs(self.latitude) > POLAR_LIMIT_DEG:
            raise PolarLatitudeError(
                f"Placidus house cusps are undefined beyond +/-{POLAR_LIMIT_DEG}deg "
                f"latitude (got {self.latitude:.4f}). Choose another house system."
            )
        if not -14.0 <= self.tz_offset_hours <= 14.0:
            raise ValueError(f"implausible tz offset: {self.tz_offset_hours}")
        _dt.datetime(self.year, self.month, self.day,
                     self.hour, self.minute, self.second)   # validates the date

    @property
    def local_datetime(self) -> _dt.datetime:
        return _dt.datetime(self.year, self.month, self.day,
                            self.hour, self.minute, self.second)

    @property
    def julian_day_ut(self) -> float:
        ut = (self.hour + self.minute / 60.0 + self.second / 3600.0
              - self.tz_offset_hours)
        return swe.julday(self.year, self.month, self.day, ut)

    @property
    def geopos(self) -> tuple[float, float, float]:
        return (self.longitude, self.latitude, self.altitude_m)

    @classmethod
    def from_zone(cls, date_str: str, time_str: str, lat: float, lon: float,
                  tzname: str, ayanamsa: "KPAyanamsa" = None) -> "BirthInput":
        """Build from an IANA timezone name, matching core.Chart's handling.

        The UTC offset is resolved *at the birth moment*, so historical DST and
        wartime offsets are applied the same way the Lahiri engine applies them.
        """
        from zoneinfo import ZoneInfo
        local = _dt.datetime.fromisoformat(f"{date_str}T{time_str}")
        local = local.replace(tzinfo=ZoneInfo(tzname))
        offset = local.utcoffset()
        hours = offset.total_seconds() / 3600.0 if offset else 0.0
        return cls(
            year=local.year, month=local.month, day=local.day,
            hour=local.hour, minute=local.minute, second=local.second,
            tz_offset_hours=hours, latitude=lat, longitude=lon,
            ayanamsa=ayanamsa if ayanamsa is not None else KPAyanamsa.CLASSIC,
        )

    def shifted(self, minutes: float) -> "BirthInput":
        """Return a new BirthInput offset by N minutes. Used by sensitivity
        scanning. Never mutates self."""
        dt = self.local_datetime + _dt.timedelta(minutes=minutes)
        return BirthInput(
            year=dt.year, month=dt.month, day=dt.day,
            hour=dt.hour, minute=dt.minute, second=dt.second,
            tz_offset_hours=self.tz_offset_hours,
            latitude=self.latitude, longitude=self.longitude,
            altitude_m=self.altitude_m, ayanamsa=self.ayanamsa,
        )

    def cache_key(self) -> tuple:
        """Stable key for st.cache_data. Ayanamsa is part of it -- switching it
        must invalidate the cache."""
        return (self.year, self.month, self.day, self.hour, self.minute,
                self.second, self.tz_offset_hours, round(self.latitude, 6),
                round(self.longitude, 6), int(self.ayanamsa))
