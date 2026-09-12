KUNDALI GENERATOR — WEB APP
===========================
Requirements: Python 3.9+ (3.11 recommended)

DEPLOY (free, shareable URL)
----------------------------
1. Push every file in this zip to the ROOT of a GitHub repo (not a subfolder).
2. share.streamlit.io -> sign in with GitHub -> "Create app".
3. Repository = your repo, Branch = main, Main file path = app.py.
   (It defaults to streamlit_app.py, which does not exist here — change it.)
4. Deploy. First build takes ~3-5 min: pyswisseph compiles from source.
   If the build fails, open Advanced settings and select Python 3.11.
Private repos work, but the free tier allows only ONE private-repo app.

RUN LOCALLY
-----------
  pip install -r requirements.txt
  streamlit run app.py

CLI
---
  python3 generate_kundali.py --dob 1991-09-16 --time 22:50 \
      --place "Naya Nangal" --country IN --name "Full Name"
  python3 generate_kundali.py --dob 1991-09-16 --time 22:50 \
      --lat 31.3897 --lon 76.3757 --tz Asia/Kolkata --place-label "Nangal"
Times are 24-hour. 10:50 PM = 22:50.

FILES
-----
app.py               Streamlit UI (page switch: report / numerology / KP)
birth_form.py        shared date/time/place form used by the report and KP pages
kp/                  Krishnamurti Paddhati engine (see kp/README.md)
tests/               pytest suite: 51 tests, incl. cross-engine isolation
generate_kundali.py  build_report() + CLI
core.py              ephemeris, ayanamsa guard, geocoder, panchanga,
                     divisional charts, Jaimini
strength.py          Shadbala, Bhava Bala, Ashtakavarga
dasha.py             Vimshottari
tables.py            lookup data
diagnose.py          prints the sidereal mode actually in effect; run this
                     if any output looks shifted
requirements.txt     dependencies

VALIDATION STATUS
-----------------
Verified against a third-party app on a real chart (16 Sep 1991):
  - all 8 sign placements (7 planets + Lagna)
  - all 84 Bhinnashtakavarga cells and the SAV row
Verified internally:
  - BAV table invariants (48/49/39/54/56/52/39, total 337)
  - Lahiri ayanamsa against reference epochs (1956, 2000)
  - no crashes across polar, southern-hemisphere, 1850, 2050, leap-day,
    wartime-DST and dateline births
NOT externally validated:
  - Shadbala and Bhava Bala. Treat as indicative, not authoritative.

KNOWN APPROXIMATIONS (by impact)
--------------------------------
1. Kala Bala: Masa and Abda lords are stubbed to the Vara lord. Up to
   45 virupas per planet; can move Shadbala rankings. Largest known gap.
2. Benefic/malefic set is fixed. Mercury's status should depend on
   association and the Moon's on paksha. Affects Drik and Paksha Bala.
3. Cheshta Bala uses the Vakradi 8-fold motion classification rather than
   the true-motion formula. A legitimate variant; differs from some tools.
4. Bhava Dig Bala treats Sagittarius and Capricorn whole instead of
   splitting them by half.
5. Ashtakavarga totals are unreduced — no Trikona or Ekadhipatya shodhana.
6. Ambiguous local times (the repeated hour at a DST fall-back) resolve
   silently to the first occurrence.

CONVENTIONS
-----------
Lahiri (Chitrapaksha) ayanamsa, sidereal zodiac, whole-sign houses,
true node for Rahu, 7-karaka Chara scheme, Vimshottari year = 365.2425 d.
Ashtakavarga grids are printed BOTH by sign and by house. Note that many
apps label this grid "RN" meaning Rashi Number (Aries = 1), which is NOT
the house number unless the Lagna is in Aries.

VEDIC NUMEROLOGY (ANK JYOTISH) — added as a separate section
------------------------------------------------------------
Independent of Vimshottari. Uses the calendar date of birth only: no
birth time, coordinates or ephemeris. The two dasha systems will not
agree and are not meant to.

Rules (per published Ank Jyotish method, validated against two charts):
  Mulank      digit sum of the birth DAY, reduced to 1-9
  Bhagyank    digit sum of the whole birth DATE, reduced to 1-9
  3x3 grid    digits of DD MM YY (two-digit year, zeros dropped) plus
              Mulank and Bhagyank, each in its planet's fixed cell:
                 Thought  Will   Action
      Mental       3 Jup   1 Sun  9 Mars
      Emotion      6 Ven   7 Ket  5 Mer
      Practical    2 Moo   8 Sat  4 Rah
  Mahadasha   starts at the Mulank, then cycles 1-9; each lasts as many
              years as its own number. Full cycle = 45 years, repeating.
  Antardasha  one per year, birthday to birthday:
              reduce(reduced birth day + birth month
                     + reduced last two digits of the year
                     + weekday number of that year's birthday)
              Weekday numbers: Sun 1, Mon 2, Tue 9, Wed 5, Thu 3,
              Fri 6, Sat 8.
  Pratyantar  9 per Antardasha, starting at the Antardasha number and
              cycling 1-9. Fixed durations in days:
              1:8  2:16  3:24  4:32  5:41  6:49  7:57  8:65  9:73
              (total 365)
  Daily Dasha reduce(active Pratyantar number + weekday number)

VALIDATION: grid, Mahadasha spans, all 21 observed Antardasha numbers
and all 9 Pratyantardasha date boundaries reproduce a reference app
exactly, across two independent birth dates.


KP CHART PAGE (added)
---------------------
Third page on the top switcher. Krishnamurti Paddhati: Krishnamurti ayanamsa,
Placidus cusps, 243 star/sub spans, four-level significators, ruling planets,
and a birth-time precision panel.

Deliberate divergences from the Kundali report page, both stated in the KP
page caption:
  - ayanamsa   KP uses Krishnamurti (classic), the report uses Lahiri
  - houses     KP uses Placidus cusps, the report uses whole-sign
  - node       KP uses the MEAN node, the report uses the TRUE node
House placements will therefore differ between the two pages. That is correct,
not a bug. To make the node agree, set _NODE in kp/ephemeris.py to
swe.TRUE_NODE and regenerate the golden fixture.

SIDEREAL MODE SAFETY
--------------------
Swiss Ephemeris holds the sidereal mode as write-only global state -- there is
no getter. Two independent guards now cover it:
  1. core.py calls _lahiri() immediately before every sidereal calculation and
     ayanamsa_check() re-asserts then verifies, so it is self-healing.
  2. kp/ tracks the mode itself and restores the previous value in a finally
     block; app.py calls configure_default(swe.SIDM_LAHIRI) at startup.
tests/test_integration.py proves a full Kundali report is byte-identical before
and after KP work, including after a KP exception.

RUNNING THE TESTS
-----------------
  pip install pytest
  python -m pytest tests/ -q

tests/test_app_pages.py drives the real Streamlit widgets via
streamlit.testing.v1.AppTest. A plain "does the server return 200" boot check
does NOT execute page code and will miss render-time errors -- run this suite
before every push.

Note: kp/render.py deliberately does NOT use st.cache_data. KPChart holds a
MappingProxyType (the read-only planet mapping), which cannot be pickled, and
st.cache_data pickles its return value. Building a chart costs ~0.5 ms and a
full sensitivity scan ~2.5 ms, so there is nothing to cache.
