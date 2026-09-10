# -*- coding: utf-8 -*-
"""
Vedic numerology (Ank Jyotish) — 3x3 grid and the numerology dasha system.

This is a SEPARATE system from Vimshottari. It needs only the calendar date
of birth: no birth time, no coordinates, no ephemeris.

Rules implemented (see METHOD notes at the bottom of the report section):
  Mulank    = digit sum of the birth DAY, reduced to 1-9
  Bhagyank  = digit sum of the whole birth DATE, reduced to 1-9
  Grid      = digits of DD MM YY (two-digit year, zeros dropped)
              plus Mulank and Bhagyank, each placed in its planet's cell
  Mahadasha = starts at the Mulank, then cycles 1..9; each lasts as many
              years as its own number (so a full cycle is 45 years)
  Antardasha= one per year, birthday to birthday, numbered
              reduce(reduced birth day + birth month
                     + reduced last two digits of the year
                     + weekday number of that year's birthday)
  Pratyantar= 9 per Antardasha, starting at the Antardasha number and
              cycling 1..9, with fixed classical durations summing to 365
  Daily     = reduce(active Pratyantar number + weekday number)
"""
import datetime as dt

PLANET = {1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
          6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars"}

SANSKRIT = {1: "Surya", 2: "Chandra", 3: "Guru", 4: "Rahu", 5: "Budh",
            6: "Shukra", 7: "Ketu", 8: "Shani", 9: "Mangal"}

# Vedic weekday numbers (note: these are planet numbers, not 1-7)
WEEKDAY_NUM = {"Sunday": 1, "Monday": 2, "Tuesday": 9, "Wednesday": 5,
               "Thursday": 3, "Friday": 6, "Saturday": 8}

# Classical Pratyantardasha durations in days; these sum to exactly 365
PD_DAYS = {1: 8, 2: 16, 3: 24, 4: 32, 5: 41, 6: 49, 7: 57, 8: 65, 9: 73}

# The 3x3 grid: fixed planet per cell.
#   Thought   Will    Action
#   3 Jupiter 1 Sun   9 Mars      <- Mental
#   6 Venus   7 Ketu  5 Mercury   <- Emotion
#   2 Moon    8 Saturn 4 Rahu     <- Practical
GRID = [[3, 1, 9], [6, 7, 5], [2, 8, 4]]
ROW_LABEL = ["Mental", "Emotion", "Practical"]
COL_LABEL = ["Thought", "Will", "Action"]


def reduce_digits(n):
    """Digital root, 1-9 (0 only for input 0)."""
    n = abs(int(n))
    while n > 9:
        n = sum(int(c) for c in str(n))
    return n


def mulank(dob):
    return reduce_digits(dob.day)


def bhagyank(dob):
    return reduce_digits(sum(int(c) for c in dob.strftime("%d%m%Y")))


def grid_digits(dob):
    """Digits that populate the 3x3 grid, in order, with repeats kept."""
    s = dob.strftime("%d%m%y")
    out = [int(c) for c in s if c != "0"]
    out.append(mulank(dob))
    out.append(bhagyank(dob))
    return out


def grid_counts(dob):
    counts = {n: 0 for n in range(1, 10)}
    for d in grid_digits(dob):
        counts[d] += 1
    return counts


def mahadashas(dob, count=9):
    """Successive Mahadashas from birth. Returns list of dicts."""
    out = []
    num = mulank(dob)
    start = dob
    age = 0
    for _ in range(count):
        end = _add_years(dob, age + num)
        out.append({"number": num, "planet": PLANET[num], "start": start,
                    "end": end, "years": num, "age_from": age,
                    "age_to": age + num})
        age += num
        start = end
        num = num % 9 + 1
    return out


def _add_years(d, n):
    try:
        return d.replace(year=d.year + n)
    except ValueError:          # 29 Feb
        return d.replace(year=d.year + n, day=28)


def antardasha_number(dob, year):
    """Antardasha for the personal year beginning on the birthday in `year`."""
    d = reduce_digits(dob.day)
    m = dob.month
    y = reduce_digits(int(str(year)[-2:]))
    try:
        bday = dt.date(year, dob.month, dob.day)
    except ValueError:
        bday = dt.date(year, dob.month, 28)
    w = WEEKDAY_NUM[bday.strftime("%A")]
    return reduce_digits(d + m + y + w), (d, m, y, w)


def antardashas(dob, from_year, to_year):
    out = []
    for y in range(from_year, to_year + 1):
        n, parts = antardasha_number(dob, y)
        try:
            start = dt.date(y, dob.month, dob.day)
        except ValueError:
            start = dt.date(y, dob.month, 28)
        end = _add_years(start, 1) - dt.timedelta(days=1)
        out.append({"number": n, "planet": PLANET[n], "start": start,
                    "end": end, "year": y, "parts": parts})
    return out


def pratyantardashas(ad_number, ad_start):
    """9 sub-periods starting at the Antardasha number, cycling 1..9."""
    out = []
    t = ad_start
    num = ad_number
    for _ in range(9):
        days = PD_DAYS[num]
        end = t + dt.timedelta(days=days - 1)
        out.append({"number": num, "planet": PLANET[num], "start": t,
                    "end": end, "days": days})
        t = end + dt.timedelta(days=1)
        num = num % 9 + 1
    return out


def daily_dasha(pd_number, day):
    return reduce_digits(pd_number + WEEKDAY_NUM[day.strftime("%A")])


def active(dob, on=None):
    """The operating MD / AD / PD / DD on a given date."""
    on = on or dt.date.today()
    md = next((m for m in mahadashas(dob, 40)
               if m["start"] <= on < m["end"]), None)
    pyear = on.year if (on.month, on.day) >= (dob.month, dob.day) else on.year - 1
    ad = antardashas(dob, pyear, pyear)[0]
    pd = next((p for p in pratyantardashas(ad["number"], ad["start"])
               if p["start"] <= on <= p["end"]), None)
    dd = daily_dasha(pd["number"], on) if pd else None
    return {"date": on, "MD": md, "AD": ad, "PD": pd,
            "DD": {"number": dd, "planet": PLANET[dd]} if dd else None}


def cell_digits(dob, overlay=None):
    """Per-cell digit strings tagged by source.

    Returns {number: [(digit, source), ...]} where source is one of
    'natal', 'md', 'ad', 'pd'. `overlay` is a dict like
    {'md': 5, 'ad': 2, 'pd': 7} — any subset.
    """
    out = {n: [] for n in range(1, 10)}
    for d in grid_digits(dob):
        out[d].append((d, "natal"))
    for src in ("md", "ad", "pd"):
        if overlay and overlay.get(src):
            v = overlay[src]
            out[v].append((v, src))
    return out


def render_grid(dob, extra=None):
    """3x3 grid as text lines. `extra` is a list of digits to overlay."""
    counts = grid_counts(dob)
    if extra:
        for e in extra:
            counts[e] += 1
    lines = []
    lines.append(f"{'':<11}{'Thought':^15}{'Will':^15}{'Action':^15}")
    for r in range(3):
        cells = []
        for c in range(3):
            n = GRID[r][c]
            cells.append(str(n) * counts[n] if counts[n] else "-")
        lines.append(f"{ROW_LABEL[r]:<11}" + "".join(f"{x:^15}" for x in cells))
        lines.append(f"{'':<11}" +
                     "".join(f"{'('+PLANET[GRID[r][c]]+')':^15}" for c in range(3)))
    return lines
