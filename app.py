# -*- coding: utf-8 -*-
"""Streamlit front-end for the kundali generator."""
import datetime as dt
import streamlit as st
from generate_kundali import build_report
from core import geocode_candidates

st.set_page_config(page_title="Kundali Generator", page_icon="🔯",
                   layout="centered")

st.title("Kundali Generator")
st.caption("Lahiri ayanamsa · whole-sign houses · Swiss Ephemeris · fully offline")

page = st.radio("", ["Kundali report", "Vedic numerology"],
                horizontal=True, label_visibility="collapsed")

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

name = st.text_input("Full name (optional)",
                     help="Only used for the Chaldean / Pythagorean name numbers")

c1, c2 = st.columns(2)
with c1:
    dob = st.date_input("Date of birth", value=dt.date(1990, 1, 1),
                        min_value=dt.date(1800, 1, 1),
                        max_value=dt.date(2100, 12, 31), format="DD/MM/YYYY")
with c2:
    tob = st.time_input("Time of birth (24h, local)", value=dt.time(12, 0), step=60)

mode = st.radio("Birth place", ["Search by name", "Enter coordinates"],
                horizontal=True)

loc = None
if mode == "Search by name":
    p1, p2 = st.columns([3, 1])
    with p1:
        query = st.text_input("Town / City", placeholder="e.g. Naya Nangal")
    with p2:
        country = st.text_input("Country", value="IN", help="2-letter code")

    if query.strip():
        cands = geocode_candidates(query.strip(), country.strip() or None, limit=8)
        if not cands:
            st.warning(
                "No match. The offline database only covers towns above roughly "
                "15,000 people. Try the nearest larger town — anything within "
                "~25 km makes no practical difference to the chart — or switch "
                "to **Enter coordinates**.")
        else:
            labels = [f"{c['name']} ({c['country']}) · {c['lat']:.2f}, "
                      f"{c['lon']:.2f} · {c['tz']}" for c in cands]
            pick = st.selectbox("Closest matches — pick the right one", labels)
            loc = cands[labels.index(pick)]
            if loc["name"].lower() != query.strip().lower():
                st.caption(f"'{query.strip()}' isn't listed separately; using "
                           f"**{loc['name']}**.")
else:
    p1, p2, p3 = st.columns(3)
    with p1:
        lat = st.number_input("Latitude", value=28.6654, format="%.4f")
    with p2:
        lon = st.number_input("Longitude", value=77.4391, format="%.4f")
    with p3:
        tzname = st.text_input("Timezone", value="Asia/Kolkata",
                               help="IANA name, e.g. Asia/Kolkata")
    label = st.text_input("Place label (for the report header)", value="")
    loc = {"lat": lat, "lon": lon, "tz": tzname.strip(), "label": label.strip()}

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
