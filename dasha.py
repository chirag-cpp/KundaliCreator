# -*- coding: utf-8 -*-
"""Vimshottari dasha: MD -> AD -> PD tree; Sookshma & Prana for current chain."""
import datetime as dt
from tables import DASHA_YEARS, DASHA_ORDER, NAK_LORDS

YEAR_DAYS = 365.2425

def _sub_periods(lord, start, span_days):
    """Split a period of span_days ruled by `lord` into 9 sub-periods."""
    i = DASHA_ORDER.index(lord)
    out = []
    t = start
    for k in range(9):
        sub = DASHA_ORDER[(i + k) % 9]
        d = span_days * DASHA_YEARS[sub] / 120.0
        out.append((sub, t, t + dt.timedelta(days=d)))
        t += dt.timedelta(days=d)
    return out

def vimshottari(chart, depth_now=None):
    """Return MD list with nested AD/PD; plus current chain to Prana."""
    moon = chart.pos["Moon"]
    nak = int(moon // (360 / 27))
    frac = (moon % (360 / 27)) / (360 / 27)
    lord = NAK_LORDS[nak]
    balance = DASHA_YEARS[lord] * (1 - frac)
    birth = chart.local.replace(tzinfo=None)
    # Mahadashas covering 120y from birth
    mds = []
    start = birth - dt.timedelta(days=DASHA_YEARS[lord] * frac * YEAR_DAYS)
    i = DASHA_ORDER.index(lord)
    t = start
    for k in range(9):
        md = DASHA_ORDER[(i + k) % 9]
        d = DASHA_YEARS[md] * YEAR_DAYS
        mds.append({"lord": md, "start": t, "end": t + dt.timedelta(days=d)})
        t += dt.timedelta(days=d)
    # nest AD and PD
    for md in mds:
        span = (md["end"] - md["start"]).days + \
               (md["end"] - md["start"]).seconds / 86400
        ads = _sub_periods(md["lord"], md["start"], span)
        md["antardashas"] = []
        for (al, s, e) in ads:
            ad = {"lord": al, "start": s, "end": e, "pratyantar": []}
            pds = _sub_periods(al, s, (e - s).total_seconds() / 86400)
            for (pl, ps, pe) in pds:
                ad["pratyantar"].append({"lord": pl, "start": ps, "end": pe})
            md["antardashas"].append(ad)
    # current chain down to Prana
    now = dt.datetime.now()
    chain = _current_chain(mds, now)
    return {"balance_lord": lord, "balance_years": balance,
            "mahadashas": mds, "current": chain, "as_of": now}

def _current_chain(mds, now):
    def find(periods, key):
        for p in periods:
            if p["start"] <= now < p["end"]:
                return p
        return None
    md = find(mds, None)
    if not md: return None
    ad = find(md["antardashas"], None)
    pd = find(ad["pratyantar"], None)
    # sookshma under pd
    sos = _sub_periods(pd["lord"], pd["start"],
                       (pd["end"] - pd["start"]).total_seconds() / 86400)
    so = next(((l, s, e) for (l, s, e) in sos if s <= now < e), sos[-1])
    prs = _sub_periods(so[0], so[1], (so[2] - so[1]).total_seconds() / 86400)
    pr = next(((l, s, e) for (l, s, e) in prs if s <= now < e), prs[-1])
    return {"Mahadasha": md, "Antardasha": ad, "Pratyantardasha": pd,
            "Sookshma": {"lord": so[0], "start": so[1], "end": so[2]},
            "Prana": {"lord": pr[0], "start": pr[1], "end": pr[2]}}
