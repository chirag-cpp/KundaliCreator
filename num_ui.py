# -*- coding: utf-8 -*-
"""Streamlit UI for the Vedic numerology page (grid + MD/AD/PD cards)."""
import datetime as dt
import streamlit as st
import numerology as NU

COLOR = {"natal": "#c9d4e2", "md": "#4a9eff", "ad": "#4ade80", "pd": "#fb923c"}

CSS = """
<style>
/* fixed geometry so a table can never overflow its column */
.ngwrap{max-width:460px}
table.numgrid{table-layout:fixed;border-collapse:collapse;width:100%}
table.numgrid td{border:1px solid #2b3648;text-align:center;
  vertical-align:middle;padding:8px 2px;height:56px;overflow:hidden}
table.numgrid td.dg{font-size:20px;letter-spacing:1px;line-height:1.15}
table.numgrid td .pl{display:block;font-size:10px;color:#6b7a90;
  letter-spacing:0;margin-top:3px;white-space:nowrap}
table.numgrid td.axis{border:none;color:#8fa0b8;font-size:11px;
  white-space:nowrap;width:74px;text-align:right;padding-right:8px}
table.numgrid td.head{border:none;color:#8fa0b8;font-size:11px;
  white-space:nowrap;height:22px;padding:0}
.card{border:1px solid #2b3648;border-radius:8px;background:#111823;
  margin-bottom:6px;overflow:hidden}
.card .hd{background:#161f2e;padding:6px 8px;font-size:11.5px;
  color:#9fb0c8;text-align:center;border-bottom:1px solid #2b3648;
  line-height:1.3;min-height:34px}
.card table.numgrid td{height:40px;padding:4px 2px}
.card table.numgrid td.dg{font-size:17px}
.legend{font-size:12px;color:#8fa0b8;margin:0 0 10px 0}
.subtle{color:#6b7a90;font-size:12px;margin-bottom:14px}
</style>
"""


def _cell(dob, n, overlay, planet):
    parts = NU.cell_digits(dob, overlay)[n]
    if parts:
        inner = "".join(f"<span style='color:{COLOR[s]}'>{d}</span>"
                        for d, s in parts)
    else:
        inner = "<span style='color:#39445a'>&middot;</span>"
    pl = f"<span class='pl'>{NU.PLANET[n]}</span>" if planet else ""
    return f"<td class='dg'>{inner}{pl}</td>"


def grid_html(dob, overlay=None, axes=False, planet=False):
    rows = []
    if axes:
        rows.append("<tr><td class='head'></td>" +
                    "".join(f"<td class='head'>{c}</td>"
                            for c in NU.COL_LABEL) + "</tr>")
    for r in range(3):
        lab = f"<td class='axis'>{NU.ROW_LABEL[r]}</td>" if axes else ""
        cells = "".join(_cell(dob, NU.GRID[r][c], overlay, planet)
                        for c in range(3))
        rows.append(f"<tr>{lab}{cells}</tr>")
    return f"<table class='numgrid'>{''.join(rows)}</table>"


def card_html(dob, header, overlay):
    return (f"<div class='card'><div class='hd'>{header}</div>"
            f"{grid_html(dob, overlay)}</div>")


def _f(d):
    return d.strftime("%d %b %Y")


def render(dob):
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown("##### Birth grid")
    st.markdown(
        f"<div class='ngwrap'>{grid_html(dob, axes=True, planet=True)}</div>",
        unsafe_allow_html=True)

    m, b = NU.mulank(dob), NU.bhagyank(dob)
    c1, c2 = st.columns(2)
    c1.metric("Basic Number (Mulank)", f"{m} · {NU.PLANET[m]}")
    c2.metric("Destiny Number (Bhagyank)", f"{b} · {NU.PLANET[b]}")
    cnt = NU.grid_counts(dob)
    miss = [str(n) for n in range(1, 10) if cnt[n] == 0]
    rep = [f"{n}x{cnt[n]}" for n in range(1, 10) if cnt[n] > 1]
    st.caption(f"Missing: {', '.join(miss) or 'none'}  ·  "
               f"Repeated: {', '.join(rep) or 'none'}")

    st.divider()

    mds = NU.mahadashas(dob, 18)
    today = dt.date.today()
    cur = next((i for i, x in enumerate(mds)
                if x["start"] <= today < x["end"]), 0)
    labels = [f"MD {x['number']} · {x['planet']} · "
              f"{x['start'].year}-{x['end'].year}" for x in mds]
    md = mds[labels.index(st.selectbox("Mahadasha", labels, index=cur))]

    st.markdown(
        "<div class='legend'>Digits &mdash; "
        f"<b style='color:{COLOR['natal']}'>natal</b> &middot; "
        f"<b style='color:{COLOR['md']}'>Mahadasha</b> &middot; "
        f"<b style='color:{COLOR['ad']}'>Antra</b> &middot; "
        f"<b style='color:{COLOR['pd']}'>Pratyantra</b></div>",
        unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["Mahadasha", "Antra", "Pratyantra"])

    with t1:
        left, _ = st.columns([1, 2])
        with left:
            st.markdown(
                card_html(dob, f"{_f(md['start'])} - {_f(md['end'])}",
                          {"md": md["number"]}), unsafe_allow_html=True)
        st.caption(f"MD {md['number']} ({md['planet']}) — {md['years']} years, "
                   f"ages {md['age_from']}-{md['age_to']}")

    ads = NU.antardashas(dob, md["start"].year,
                         md["start"].year + md["years"] - 1)

    with t2:
        for i in range(0, len(ads), 3):
            cols = st.columns(3)
            for col, a in zip(cols, ads[i:i + 3]):
                with col:
                    st.markdown(
                        card_html(dob,
                                  f"{_f(a['start'])} -<br>{_f(a['end'])}",
                                  {"md": md["number"], "ad": a["number"]}),
                        unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='subtle'>AD {a['number']} {a['planet']}"
                        f"</div>", unsafe_allow_html=True)

    with t3:
        al = [f"{_f(a['start'])} - {_f(a['end'])}  ·  AD {a['number']} "
              f"{a['planet']}" for a in ads]
        ad = ads[al.index(st.selectbox("Antra", al, key="antra_pick"))]
        pds = NU.pratyantardashas(ad["number"], ad["start"])
        for i in range(0, 9, 3):
            cols = st.columns(3)
            for col, p in zip(cols, pds[i:i + 3]):
                with col:
                    st.markdown(
                        card_html(dob,
                                  f"{_f(p['start'])} -<br>{_f(p['end'])}",
                                  {"md": md["number"], "ad": ad["number"],
                                   "pd": p["number"]}),
                        unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='subtle'>PD {p['number']} {p['planet']} "
                        f"· {p['days']}d</div>", unsafe_allow_html=True)
