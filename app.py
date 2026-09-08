# -*- coding: utf-8 -*-
"""Streamlit front-end for the kundali generator."""
import datetime as dt
import streamlit as st
from generate_kundali import build_report
from core import geocode

st.set_page_config(page_title="Kundali Generator", page_icon="🔯",
                   layout="centered")

st.title("Kundali Generator")
st.caption("Lahiri ayanamsa · whole-sign houses · Swiss Ephemeris")

with st.form("birth"):
    name = st.text_input("Full name (optional)",
                         help="Only needed for Chaldean / Pythagorean name numbers")

    c1, c2 = st.columns(2)
    with c1:
        dob = st.date_input("Date of birth",
                            value=dt.date(1990, 1, 1),
                            min_value=dt.date(1800, 1, 1),
                            max_value=dt.date(2100, 12, 31),
                            format="DD/MM/YYYY")
    with c2:
        tob = st.time_input("Time of birth (24h, local)",
                            value=dt.time(12, 0), step=60)

    mode = st.radio("Birth place input",
                    ["City name", "Latitude / longitude"], horizontal=True)

    if mode == "City name":
        p1, p2 = st.columns([2, 1])
        with p1:
            place = st.text_input("Town / City", placeholder="e.g. Ghaziabad")
        with p2:
            country = st.text_input("Country code", value="IN",
                                    help="2-letter ISO code, e.g. IN, US, AE")
        lat = lon = tzname = None
    else:
        p1, p2, p3 = st.columns(3)
        with p1:
            lat = st.number_input("Latitude", value=28.6654, format="%.4f")
        with p2:
            lon = st.number_input("Longitude", value=77.4391, format="%.4f")
        with p3:
            tzname = st.text_input("Timezone", value="Asia/Kolkata",
                                   help="IANA name, e.g. Asia/Kolkata")
        place = st.text_input("Place label (for the report header)", value="")
        country = None

    go = st.form_submit_button("Generate report", type="primary")

if go:
    try:
        with st.spinner("Computing…"):
            kwargs = dict(dob=dob.isoformat(),
                          time=tob.strftime("%H:%M"),
                          name=name.strip() or None)
            if mode == "City name":
                if not place.strip():
                    st.error("Please enter a town or city name.")
                    st.stop()
                kwargs.update(place=place.strip(),
                              country=(country or "").strip() or None)
                loc = geocode(kwargs["place"], None, kwargs["country"])
                st.info(f"Resolved to **{loc['name']}** ({loc['country']}) — "
                        f"{loc['lat']:.4f}, {loc['lon']:.4f} · {loc['tz']}. "
                        "If that's the wrong town, use latitude / longitude instead.")
            else:
                kwargs.update(lat=lat, lon=lon, tz=tzname.strip(),
                              place_label=place.strip())

            report = build_report(**kwargs)

        fname = f"kundali_{name.strip().replace(' ', '_') or 'chart'}_{dob}.txt"
        st.download_button("Download .txt", report, file_name=fname,
                           mime="text/plain", type="primary")
        st.text(report)

    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Could not generate the report: {e}")

st.divider()
st.caption(
    "Shadbala and Bhava Bala conventions vary between software; small numeric "
    "differences are expected and the rankings are the robust output. "
    "See the Conventions section at the end of the report."
)
