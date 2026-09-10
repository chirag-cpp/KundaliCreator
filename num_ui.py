# -*- coding: utf-8 -*-
"""Streamlit UI for the Vedic numerology page (grid + MD/AD/PD cards)."""
import datetime as dt
import streamlit as st
import numerology as NU

COLOR = {"natal": "#c9d4e2", "md": "#4a9eff", "ad": "#4ade80", "pd": "#fb923c"}

CSS = """
<style>
.numgrid{border-collapse:collapse;width:100%}
.numgrid td{border:1px solid #2b3648;text-align:center;vertical-align:middle;
  padding:10px 4px;font-size:20px;letter-spacing:1px;height:52px}
.numgrid td .pl{display:block;font-size:11px;color:#6b7a90;letter-spacing:0;
  margin-top:2px}
.axis{color:#8fa0b8;font-size:12px;border:none !important}
.card{border:1px solid #2b3648;border-radius:8px;margin-bottom:14px;
  overflow:hidden;background:#111823}
.card .hd{background:#161f2e;padding:7px 10px;font-size:12.5px;
  color:#9fb0c8;text-align:center;border-bottom:1px solid #2b3648}
.card td{height:44px;font-size:18px;padding:6px 2px}
.legend{font-size:12px;color:#8fa0b8;margin:2px 0 14px 0}
.legend b{font-weight:600}
</style>
"""


def _cell_html(dob, n, overlay, show_planet):
    parts = NU.cell_digits(dob, overlay)[n]
    if not parts:
        inner = "<span style='color:#3a4557'>·</span>"
    else:
        inner = "".join(
            f"<span style='color:{COLOR[src]}'>{d}</span>" for d, src in parts)
    pl = f"<span class='pl'>{NU.PLANET[n]}</span>" if show_planet else ""
    return f"<td>{inner}{pl}</td>"


def grid_html(dob, overlay=None, axes=False, show_planet=False):
    rows = []
    if axes:
        rows.append("<tr><td class='axis'></td>" +
                    "".join(f"<td class='axis'>{c} ↓</td>"
                            for c in NU.COL_LABEL) + "</tr>")
    for r in range(3):
        cells = "".join(_cell_html(dob, NU.GRID[r][c], overlay, show_planet)
                        for c in range(3))
        lab = (f"<td class='axis'>{NU.ROW_LABEL[r]} →</td>") if axes else ""
        rows.append(f"<tr>{lab}{cells}</tr>")
    return f"<table class='numgrid'>{''.join(rows)}</table>"


def card_html(dob, header, overlay):
    return (f"<div class='card'><div class='hd'>{header}</div>"
            f"{grid_html(dob, overlay)}</div>")


def _fmt(d):
    return d.strftime("%d %b %Y")


def render(dob):
    st.markdown(CSS, unsafe_allow_html=True)
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.markdown(grid_html(dob, axes=True, show_planet=True),
                    unsafe_allow_html=True)
        st.markdown(
            f"<div style='margin-top:10px;font-size:14px'>"
            f"<b style='color:#a78bfa'>Basic Number (Mulank): {NU.mulank(dob)}</b>"
            f" &nbsp;&nbsp; "
            f"<b style='color:#60a5fa'>Destiny Number (Bhagyank): {NU.bhagyank(dob)}</b>"
            f"</div>", unsafe_allow_html=True)
        cnt = NU.grid_counts(dob)
        miss = [str(n) for n in range(1, 10) if cnt[n] == 0]
        st.caption(f"Missing numbers: {', '.join(miss) if miss else 'none'}")

    with right:
        mds = NU.mahadashas(dob, 18)
        today = dt.date.today()
        cur_i = next((i for i, m in enumerate(mds)
                      if m["start"] <= today < m["end"]), 0)
        labels = [f"MD {m['number']} · {m['planet']} · "
                  f"{m['start'].year}–{m['end'].year}" for m in mds]
        pick = st.selectbox("Mahadasha", labels, index=cur_i,
                            label_visibility="collapsed")
        md = mds[labels.index(pick)]

        st.markdown(
            f"<div class='legend'>Digit colours — "
            f"<b style='color:{COLOR['natal']}'>natal</b> · "
            f"<b style='color:{COLOR['md']}'>Mahadasha</b> · "
            f"<b style='color:{COLOR['ad']}'>Antra</b> · "
            f"<b style='color:{COLOR['pd']}'>Pratyantra</b>"
            f" &nbsp;|&nbsp; {_fmt(md['start'])} – {_fmt(md['end'])}</div>",
            unsafe_allow_html=True)

        tab_md, tab_ad, tab_pd = st.tabs(["Mahadasha", "Antra", "Pratyantra"])

        with tab_md:
            st.markdown(
                card_html(dob, f"{_fmt(md['start'])} - {_fmt(md['end'])}",
                          {"md": md["number"]}), unsafe_allow_html=True)
            st.caption(f"MD {md['number']} ({md['planet']}) — {md['years']} "
                       f"years, ages {md['age_from']}–{md['age_to']}")

        ads = NU.antardashas(dob, md["start"].year,
                             md["start"].year + md["years"] - 1)

        with tab_ad:
            cols = st.columns(min(4, len(ads)))
            for i, a in enumerate(ads):
                with cols[i % len(cols)]:
                    st.markdown(
                        card_html(dob, f"{_fmt(a['start'])} - {_fmt(a['end'])}",
                                  {"md": md["number"], "ad": a["number"]}),
                        unsafe_allow_html=True)

        with tab_pd:
            alabels = [f"{_fmt(a['start'])} – {_fmt(a['end'])}  "
                       f"(AD {a['number']} {a['planet']})" for a in ads]
            ai = st.selectbox("Antra", alabels, key="antra_pick")
            ad = ads[alabels.index(ai)]
            pds = NU.pratyantardashas(ad["number"], ad["start"])
            cols = st.columns(3)
            for i, p in enumerate(pds):
                with cols[i % 3]:
                    st.markdown(
                        card_html(dob,
                                  f"{_fmt(p['start'])} - {_fmt(p['end'])}",
                                  {"md": md["number"], "ad": ad["number"],
                                   "pd": p["number"]}),
                        unsafe_allow_html=True)
                    st.caption(f"PD {p['number']} {p['planet']} · {p['days']}d")
