"""Streamlit rendering for the KP tab.

Imported lazily by the app; the rest of the package has no streamlit
dependency, so the engine stays testable headless.

Layout rules enforced here:
  * no markdown tables  -- they clip at narrow widths
  * no st.columns() for tabular data
  * every column width pinned via column_config
  * no hardcoded colours (theme-safe)
  * sensitivity panel collapsed, at the bottom
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .chart import KPChart, build_chart
from .context import BirthInput, PolarLatitudeError
from .lords import format_dms
from .ruling import ruling_planets
from .sensitivity import DEFAULT_STEP_MIN, DEFAULT_WINDOW_MIN, scan
from .significators import (cuspal_checks, house_significators,
                            planet_significations)

PLANET_SEQ = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
              "Venus", "Saturn", "Rahu", "Ketu")


# --------------------------------------------------------------- caching
@st.cache_data(show_spinner=False)
def _cached_chart(key: tuple, _birth: BirthInput) -> KPChart:
    return build_chart(_birth)


@st.cache_data(show_spinner=False)
def _cached_scan(key: tuple, _birth: BirthInput, window: float, step: float):
    return scan(_birth, window, step)


# --------------------------------------------------------------- frames
def cusp_frame(chart: KPChart) -> pd.DataFrame:
    return pd.DataFrame([
        {"House": i + 1, "Longitude": c.dms, "Sign": c.sign,
         "Nakshatra": f"{c.nakshatra}-{c.pada}", "Star": c.star_lord,
         "Sub": c.sub_lord, "Sub-Sub": c.sub_sub_lord}
        for i, c in enumerate(chart.cusps)
    ])


def planet_frame(chart: KPChart) -> pd.DataFrame:
    rows = []
    for name in PLANET_SEQ:
        p = chart.planets[name]
        rows.append({
            "Planet": name, "Longitude": p.chain.dms, "Sign": p.chain.sign,
            "House": p.house, "Nakshatra": f"{p.chain.nakshatra}-{p.chain.pada}",
            "Star": p.chain.star_lord, "Sub": p.chain.sub_lord,
            "Sub-Sub": p.chain.sub_sub_lord, "R": "R" if p.retrograde else "",
        })
    return pd.DataFrame(rows)


def significator_frame(chart: KPChart) -> pd.DataFrame:
    return pd.DataFrame([
        {"House": h.house,
         "A \u2014 in star of occupant": list(h.level_a),
         "B \u2014 occupant": list(h.level_b),
         "C \u2014 in star of owner": list(h.level_c),
         "D \u2014 owner": list(h.level_d)}
        for h in house_significators(chart)
    ])


def signification_frame(chart: KPChart) -> pd.DataFrame:
    sig = planet_significations(chart)
    return pd.DataFrame([
        {"Planet": p, "Star lord": sig[p].star_lord,
         "Primary": list(sig[p].primary),
         "Secondary": list(sig[p].secondary),
         "Positional status": sig[p].positional_status}
        for p in PLANET_SEQ
    ])


def stability_frame(report) -> pd.DataFrame:
    """One row per cusp, keyed on required birth-time precision rather than a
    binary verdict -- over any wide window every cusp changes, so the binary
    form is uninformative."""
    return pd.DataFrame([
        {"House": c.house,
         "Sub lord": c.base_sub_lord,
         "Holds to": c.precision_label,
         "Exact minute needed": c.critical,
         "Changes to": [v for v in c.variants[1:]]}
        for c in report.cusps
    ])


# --------------------------------------------------------------- helpers
def _table(df: pd.DataFrame, config: dict, height: int | None = None) -> None:
    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config=config, height=height)


_LIST_COL = st.column_config.ListColumn if hasattr(
    st.column_config, "ListColumn") else st.column_config.TextColumn


# --------------------------------------------------------------- the tab
def render_kp_tab(birth: BirthInput | None) -> None:
    """Single entry point. Reads birth data from the shared input surface;
    renders nothing but its own tab."""
    if birth is None:
        st.info("Enter birth date, time and place to generate the KP chart.")
        return

    try:
        chart = _cached_chart(birth.cache_key(), birth)
    except PolarLatitudeError as exc:
        st.error(str(exc))
        return

    st.caption(
        f"Krishnamurti Paddhati \u00b7 Placidus houses \u00b7 "
        f"ayanamsa {format_dms(chart.ayanamsa_deg)} "
        f"({chart.ayanamsa_deg:.6f}\u00b0). "
        "Different ayanamsa and house system to the Vedic tab by design \u2014 "
        "house placements will not match."
    )

    st.subheader("Cusps")
    _table(cusp_frame(chart), {
        "House": st.column_config.NumberColumn(width="small"),
        "Longitude": st.column_config.TextColumn(width="medium"),
        "Sign": st.column_config.TextColumn(width="small"),
        "Nakshatra": st.column_config.TextColumn(width="medium"),
        "Star": st.column_config.TextColumn(width="small"),
        "Sub": st.column_config.TextColumn(width="small"),
        "Sub-Sub": st.column_config.TextColumn(width="small"),
    })

    st.subheader("Planets")
    _table(planet_frame(chart), {
        "Planet": st.column_config.TextColumn(width="small"),
        "Longitude": st.column_config.TextColumn(width="medium"),
        "Sign": st.column_config.TextColumn(width="small"),
        "House": st.column_config.NumberColumn(width="small"),
        "Nakshatra": st.column_config.TextColumn(width="medium"),
        "Star": st.column_config.TextColumn(width="small"),
        "Sub": st.column_config.TextColumn(width="small"),
        "Sub-Sub": st.column_config.TextColumn(width="small"),
        "R": st.column_config.TextColumn(width="small"),
    })

    st.subheader("Significators")
    st.caption("A: in star of occupant \u00b7 B: occupant \u00b7 "
               "C: in star of owner \u00b7 D: owner")
    _table(significator_frame(chart), {
        "House": st.column_config.NumberColumn(width="small"),
        "A \u2014 in star of occupant": _LIST_COL(width="large"),
        "B \u2014 occupant": _LIST_COL(width="medium"),
        "C \u2014 in star of owner": _LIST_COL(width="large"),
        "D \u2014 owner": _LIST_COL(width="medium"),
    }, height=460)

    with st.expander("Planet significations (primary / secondary)"):
        _table(signification_frame(chart), {
            "Planet": st.column_config.TextColumn(width="small"),
            "Star lord": st.column_config.TextColumn(width="small"),
            "Primary": _LIST_COL(width="medium"),
            "Secondary": _LIST_COL(width="medium"),
            "Positional status": st.column_config.CheckboxColumn(width="small"),
        })

    with st.expander("Cuspal sub lord \u2014 house group coverage"):
        st.caption("Mechanical set intersection only. No verdict is implied.")
        _table(pd.DataFrame([
            {"Matter": c.matter, "Cusp": c.cusp, "Sub lord": c.sub_lord,
             "Required": list(c.required), "Matched": list(c.matched),
             "Missing": list(c.missing)}
            for c in cuspal_checks(chart)
        ]), {
            "Matter": st.column_config.TextColumn(width="medium"),
            "Cusp": st.column_config.NumberColumn(width="small"),
            "Sub lord": st.column_config.TextColumn(width="small"),
            "Required": _LIST_COL(width="small"),
            "Matched": _LIST_COL(width="small"),
            "Missing": _LIST_COL(width="small"),
        })

    rp = ruling_planets(chart)
    st.divider()
    if rp.sunrise_resolved:
        st.markdown(
            f"**Ruling Planets** \u00b7 {' \u2192 '.join(rp.ordered())}  \n"
            f"**Lagna sub lord** \u00b7 {chart.cuspal_sub_lord(1)}"
        )
    else:
        st.warning("Sunrise could not be resolved at this location, so the "
                   "day lord is omitted from the Ruling Planets.")

    with st.expander("Birth-time precision"):
        st.caption(
            "How accurate the recorded birth time must be for each cusp sub "
            "lord to hold. Cusps move roughly 15 arcminutes per minute of "
            "clock time, so some movement is normal \u2014 what matters is the "
            "margin, not whether any change occurs."
        )
        report = _cached_scan(birth.cache_key(), birth,
                              DEFAULT_WINDOW_MIN, DEFAULT_STEP_MIN)
        if report.critical_houses:
            st.warning(report.headline())
        else:
            st.success(report.headline())
        _table(stability_frame(report), {
            "House": st.column_config.NumberColumn(width="small"),
            "Sub lord": st.column_config.TextColumn(width="small"),
            "Holds to": st.column_config.TextColumn(width="small"),
            "Exact minute needed": st.column_config.CheckboxColumn(width="small"),
            "Changes to": _LIST_COL(width="medium"),
        }, height=460)
