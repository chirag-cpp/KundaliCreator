"""Self-contained KP (Krishnamurti Paddhati) engine.

Isolation contract
------------------
  receives : BirthInput   (frozen dataclass)
  returns  : KPChart      (frozen dataclass, read-only planet mapping)
  imports  : swisseph + its own constants. Never the Lahiri chart modules.
  writes   : nothing outside this package.

Every swisseph call is wrapped in ``kp.context.sidereal_mode``, which restores
the process-global sidereal mode in a ``finally`` block.
"""
from .chart import KPChart, PlanetPosition, build_chart, house_of
from .context import (BirthInput, KPAyanamsa, PolarLatitudeError,
                      configure_default, current_mode, set_mode,
                      sidereal_mode)
from .lords import LordChain, format_dms, lords_of
from .ruling import RulingPlanets, ruling_planets
from .sensitivity import (CuspStability, SensitivityReport, scan)
from .significators import (CuspalCheck, HouseSignificators,
                            PlanetSignification, cuspal_checks,
                            house_significators, planet_significations)

__all__ = [
    "BirthInput", "KPAyanamsa", "PolarLatitudeError", "sidereal_mode",
    "set_mode", "current_mode", "configure_default",
    "LordChain", "lords_of", "format_dms",
    "KPChart", "PlanetPosition", "build_chart", "house_of",
    "HouseSignificators", "PlanetSignification", "CuspalCheck",
    "house_significators", "planet_significations", "cuspal_checks",
    "RulingPlanets", "ruling_planets",
    "SensitivityReport", "CuspStability", "scan",
]
__version__ = "0.1.0"
