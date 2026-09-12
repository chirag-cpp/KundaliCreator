# -*- coding: utf-8 -*-
"""Shared birth-input form.

Both the Kundali report and the KP chart need date, time and place. Keeping one
implementation means the two pages cannot drift apart, and the geocoder
behaviour stays identical across them.
"""
import datetime as dt

import streamlit as st

from core import geocode_candidates


def birth_form(key_prefix: str, want_name: bool = True):
    """Render the form. Returns (dob, tob, loc, name) where loc is a dict with
    lat/lon/tz and optionally label/name, or None if nothing is chosen yet."""
    name = ""
    if want_name:
        name = st.text_input(
            "Full name (optional)", key=f"{key_prefix}_name",
            help="Only used for the Chaldean / Pythagorean name numbers")

    c1, c2 = st.columns(2)
    with c1:
        dob = st.date_input("Date of birth", value=dt.date(1990, 1, 1),
                            min_value=dt.date(1800, 1, 1),
                            max_value=dt.date(2100, 12, 31),
                            format="DD/MM/YYYY", key=f"{key_prefix}_dob")
    with c2:
        tob = st.time_input("Time of birth (24h, local)", value=dt.time(12, 0),
                            step=60, key=f"{key_prefix}_tob")

    mode = st.radio("Birth place", ["Search by name", "Enter coordinates"],
                    horizontal=True, key=f"{key_prefix}_mode")

    loc = None
    if mode == "Search by name":
        p1, p2 = st.columns([3, 1])
        with p1:
            query = st.text_input("Town / City", placeholder="e.g. Naya Nangal",
                                  key=f"{key_prefix}_query")
        with p2:
            country = st.text_input("Country", value="IN", help="2-letter code",
                                    key=f"{key_prefix}_country")

        if query.strip():
            cands = geocode_candidates(query.strip(),
                                       country.strip() or None, limit=8)
            if not cands:
                st.warning(
                    "No match. The offline database only covers towns above "
                    "roughly 15,000 people. Try the nearest larger town — "
                    "anything within ~25 km makes no practical difference to "
                    "the chart — or switch to **Enter coordinates**.")
            else:
                labels = [f"{c['name']} ({c['country']}) · {c['lat']:.2f}, "
                          f"{c['lon']:.2f} · {c['tz']}" for c in cands]
                pick = st.selectbox("Closest matches — pick the right one",
                                    labels, key=f"{key_prefix}_pick")
                loc = cands[labels.index(pick)]
                if loc["name"].lower() != query.strip().lower():
                    st.caption(f"'{query.strip()}' isn't listed separately; "
                               f"using **{loc['name']}**.")
    else:
        p1, p2, p3 = st.columns(3)
        with p1:
            lat = st.number_input("Latitude", value=28.6654, format="%.4f",
                                  key=f"{key_prefix}_lat")
        with p2:
            lon = st.number_input("Longitude", value=77.4391, format="%.4f",
                                  key=f"{key_prefix}_lon")
        with p3:
            tzname = st.text_input("Timezone", value="Asia/Kolkata",
                                   help="IANA name, e.g. Asia/Kolkata",
                                   key=f"{key_prefix}_tz")
        label = st.text_input("Place label (for the report header)", value="",
                              key=f"{key_prefix}_label")
        loc = {"lat": lat, "lon": lon, "tz": tzname.strip(),
               "label": label.strip()}

    return dob, tob, loc, name
