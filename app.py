# -*- coding: utf-8 -*-
"""Streamlit front-end for the kundali generator."""
import datetime as dt

import streamlit as st
import swisseph as swe

from generate_kundali import build_report
from birth_form import birth_form

# The Lahiri engine assumes Swiss Ephemeris is left in Lahiri sidereal mode.
# The KP package tracks and restores the mode around its own calls; this tells
# it what to restore to. core.py additionally re-asserts Lahiri before every
# calculation, so the two guards are belt and braces.
from kp import configure_default
configure_default(swe.SIDM_LAHIRI)

st.set_page_config(page_title="Kundali Generator", page_icon="🔯",
                   layout="centered")

st.title("Kundali Generator")
st.caption("Lahiri ayanamsa · whole-sign houses · Swiss Ephemeris · fully offline")

page = st.radio("", ["Kundali report", "Vedic numerology", "KP chart"],
                horizontal=True, label_visibility="collapsed")

# --------------------------------------------------------------- numerology
if page == "Vedic numerology":
    import num_ui
    st.caption("Ank Jyotish — needs the date of birth only. "
               "No birth time, place or ephemeris.")
    ndob = st.date_input("Date of birth", value=dt.date(1990, 1, 1),
                         min_value=dt.date(1900, 1, 1),
                         max_value=dt.date(2100, 12, 31),
                         format="DD/MM/YYYY", key="num_dob")
    st.divider()
    num_ui.render(ndob)
    st.stop()

# ----------------------------------------------------------------- KP chart
if page == "KP chart":
    from kp import BirthInput, PolarLatitudeError
    from kp.render import render_kp_tab

    st.caption("Krishnamurti Paddhati — a different ayanamsa and house system "
               "to the Kundali report. House placements will not match, by "
               "design.")
    dob, tob, loc, _ = birth_form("kp", want_name=False)
    st.divider()

    birth = None
    if loc is not None:
        try:
            birth = BirthInput.from_zone(dob.isoformat(), tob.strftime("%H:%M"),
                                         loc["lat"], loc["lon"], loc["tz"])
        except PolarLatitudeError as exc:
            st.error(str(exc))
        except Exception as exc:                       # bad tz name etc.
            st.error(f"Could not read the birth details: {exc}")

    render_kp_tab(birth)
    st.stop()

# ------------------------------------------------------------ kundali report
dob, tob, loc, name = birth_form("rep")

if st.button("Generate report", type="primary", disabled=loc is None):
    try:
        with st.spinner("Computing…"):
            kwargs = dict(dob=dob.isoformat(), time=tob.strftime("%H:%M"),
                          name=name.strip() or None,
                          lat=loc["lat"], lon=loc["lon"], tz=loc["tz"],
                          place_label=loc.get("label") or loc.get("name", ""))
            report = build_report(**kwargs)
        fname = (f"kundali_{name.strip().replace(' ', '_') or 'chart'}"
                 f"_{dob}.txt")
        st.download_button("Download .txt", report, file_name=fname,
                           mime="text/plain", type="primary")
        st.text(report)
    except Exception as e:
        st.error(f"Could not generate the report: {e}")

st.divider()
st.caption(
    "Shadbala and Bhava Bala conventions vary between software; small numeric "
    "differences are expected and the rankings are the robust output. "
    "See the Conventions section at the end of the report."
)
