# kp — Krishnamurti Paddhati engine

Self-contained KP module for the kundali app. No network, no AI APIs.
Swiss Ephemeris (`pyswisseph`) only.

## Isolation contract

    receives : BirthInput   (frozen dataclass)
    returns  : KPChart      (frozen, read-only planet mapping)
    imports  : swisseph + own constants. Never the Lahiri chart modules.
    writes   : nothing outside this package.

`swe.set_sid_mode()` is process-global and Swiss Ephemeris exposes **no
getter** — the current mode cannot be read back. So this package owns the
state: `kp.context.set_mode()` is the only sanctioned setter, and
`sidereal_mode()` saves and restores whatever was actually in effect (not a
hardcoded default), in a `finally` block. Nesting is safe.

At startup, tell it what the rest of the engine assumes:

    from kp import configure_default
    configure_default(swe.SIDM_LAHIRI)

Then retrofit existing Lahiri call sites to wrap their swisseph calls in
`with sidereal_mode(swe.SIDM_LAHIRI):`. This is the one failure mode capable
of silently corrupting already-tested output.

## Install / test

    pip install pyswisseph pandas streamlit pytest
    python -m pytest tests/ -q

## Wiring

    from kp import BirthInput, KPAyanamsa
    from kp.render import render_kp_tab

    tab_chart, tab_numerology, tab_kp = st.tabs(["Chart", "Numerology", "KP"])
    with tab_kp:
        render_kp_tab(birth_input)

Birth data comes from the shared input surface. The KP tab renders no inputs
of its own.

## Golden tests

`tests/golden/kp_nangal_19910916.json` is the validated reference chart
(16.09.1991 22:50 IST, Nangal, Krishnamurti classic ayanamsa). Any change to
the sub table, ayanamsa handling or cusp code must leave it byte-identical.

Regenerate only after re-validating against the third-party app:

    python tests/make_golden.py

Add 3–4 more profiles as they are validated — currently there is no
southern-hemisphere, pre-1900 or high-latitude case in the set.

## Birth-time precision

Cusps move ~15 arcminutes per minute of clock time; sub spans are 40–133
arcminutes wide. Over ±5 minutes every cusp sub lord changes (measured 12/12
on unrelated charts), so a binary stable/unstable verdict carries no
information. `kp.sensitivity` therefore reports the **margin** — how accurate
the birth time must be for each cusp to hold — and flags only cusps that turn
on the recorded minute.

## Scope

In: cusps, planets (sign/star/sub/sub-sub), significator grid, planet
significations, ruling planets, birth-time precision.

Deferred: 4-step theory, horary 1–249, transit overlay, cuspal significator
ranking, interpretation text.
