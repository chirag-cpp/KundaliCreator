import json
import pathlib
import sys

import pytest
import swisseph as swe

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from kp import (BirthInput, KPAyanamsa, PolarLatitudeError, build_chart,
                house_of, house_significators, lords_of, planet_significations,
                ruling_planets, scan, sidereal_mode)
from kp.constants import (LORDS, NAK_SPAN, SUB_SPANS, TOTAL_YEARS, YEARS,
                          sub_index)
from kp.context import DEFAULT_SID_MODE

from make_golden import NANGAL, snapshot

GOLDEN = pathlib.Path(__file__).parent / "golden" / "kp_nangal_19910916.json"


# ---------------------------------------------------------------- isolation
class TestIsolation:
    """The tests that protect the existing Lahiri engine."""

    def test_sid_mode_restored_after_block(self):
        swe.set_sid_mode(DEFAULT_SID_MODE)
        before = swe.get_ayanamsa_ut(2448516.0)
        with sidereal_mode(KPAyanamsa.CLASSIC):
            assert swe.get_ayanamsa_ut(2448516.0) != before
        assert swe.get_ayanamsa_ut(2448516.0) == before

    def test_sid_mode_restored_after_exception(self):
        swe.set_sid_mode(DEFAULT_SID_MODE)
        before = swe.get_ayanamsa_ut(2448516.0)
        with pytest.raises(RuntimeError):
            with sidereal_mode(KPAyanamsa.CLASSIC):
                raise RuntimeError("boom")
        assert swe.get_ayanamsa_ut(2448516.0) == before

    def test_full_chart_build_leaves_mode_clean(self):
        swe.set_sid_mode(DEFAULT_SID_MODE)
        before = swe.get_ayanamsa_ut(2448516.0)
        chart = build_chart(NANGAL)
        ruling_planets(chart)
        house_significators(chart)
        assert swe.get_ayanamsa_ut(2448516.0) == before

    def test_birth_input_is_immutable(self):
        with pytest.raises(Exception):
            NANGAL.hour = 3

    def test_planet_mapping_is_read_only(self):
        chart = build_chart(NANGAL)
        with pytest.raises(TypeError):
            chart.planets["Sun"] = None

    def test_shifted_does_not_mutate_original(self):
        original = (NANGAL.hour, NANGAL.minute)
        NANGAL.shifted(37)
        assert (NANGAL.hour, NANGAL.minute) == original


# ------------------------------------------------------------------- tables
class TestSubTable:
    def test_partition_is_complete_and_contiguous(self):
        assert SUB_SPANS[0].start == 0.0
        assert SUB_SPANS[-1].end == pytest.approx(360.0, abs=1e-9)
        for a, b in zip(SUB_SPANS, SUB_SPANS[1:]):
            assert a.end == pytest.approx(b.start, abs=1e-9)

    def test_nine_subs_per_nakshatra(self):
        assert len(SUB_SPANS) == 243
        for n in range(27):
            assert sum(1 for s in SUB_SPANS if s.nakshatra_index == n) == 9

    def test_sub_sequence_starts_with_star_lord(self):
        for n in range(27):
            spans = [s for s in SUB_SPANS if s.nakshatra_index == n]
            assert spans[0].sub_lord == spans[0].star_lord

    def test_sub_widths_match_vimshottari_proportions(self):
        for s in SUB_SPANS:
            expected = NAK_SPAN * YEARS[s.sub_lord] / TOTAL_YEARS
            assert (s.end - s.start) == pytest.approx(expected, abs=1e-9)

    def test_known_sub_widths_in_arcminutes(self):
        """Ketu 46'40, Venus 2d13'20, Sun 40'. Guards against the 46'40 -> 40'
        transcription error found in several online sources."""
        widths = {s.sub_lord: (s.end - s.start) * 60 for s in SUB_SPANS}
        assert widths["Ketu"] == pytest.approx(46 + 40 / 60, abs=1e-6)
        assert widths["Venus"] == pytest.approx(133 + 20 / 60, abs=1e-6)
        assert widths["Sun"] == pytest.approx(40.0, abs=1e-6)

    @pytest.mark.parametrize("lon", [0.0, 359.9999, 13.3333333, 360.0, -0.0001])
    def test_lookup_never_raises(self, lon):
        assert 0 <= sub_index(lon) < 243
        lords_of(lon)

    def test_half_open_boundary(self):
        span = SUB_SPANS[0]
        assert sub_index(span.end) == 1
        assert sub_index(span.end - 1e-9) == 0


# ------------------------------------------------------------------- houses
class TestHouseAllocation:
    def test_wrap_around_zero(self):
        cusps = tuple((350.0 + i * 30.0) % 360.0 for i in range(12))
        assert house_of(cusps, 355.0) == 1
        assert house_of(cusps, 5.0) == 1
        assert house_of(cusps, 25.0) == 2

    def test_every_degree_lands_in_exactly_one_house(self):
        chart = build_chart(NANGAL)
        cusps = tuple(c.longitude for c in chart.cusps)
        for i in range(3600):
            house_of(cusps, i / 10.0)

    def test_cusp_start_belongs_to_its_own_house(self):
        chart = build_chart(NANGAL)
        cusps = tuple(c.longitude for c in chart.cusps)
        for i, c in enumerate(cusps):
            assert house_of(cusps, c) == i + 1


# ------------------------------------------------------------------ guards
class TestGuards:
    def test_polar_latitude_rejected(self):
        with pytest.raises(PolarLatitudeError):
            BirthInput(1991, 9, 16, 22, 50, 5.5, latitude=71.0, longitude=25.0)

    def test_bad_coordinates_rejected(self):
        with pytest.raises(ValueError):
            BirthInput(1991, 9, 16, 22, 50, 5.5, latitude=31.0, longitude=999.0)

    def test_invalid_date_rejected(self):
        with pytest.raises(ValueError):
            BirthInput(1991, 2, 30, 10, 0, 5.5, 31.0, 76.0)

    def test_cache_key_includes_ayanamsa(self):
        a = NANGAL.cache_key()
        b = BirthInput(**{**{f: getattr(NANGAL, f) for f in
                            ("year", "month", "day", "hour", "minute",
                             "tz_offset_hours", "latitude", "longitude")},
                          "ayanamsa": KPAyanamsa.VP291}).cache_key()
        assert a != b

    def test_nodes_always_retrograde(self):
        chart = build_chart(NANGAL)
        assert chart.planets["Rahu"].retrograde
        assert chart.planets["Ketu"].retrograde

    def test_nodes_are_exactly_opposite(self):
        chart = build_chart(NANGAL)
        d = abs(chart.planets["Rahu"].chain.longitude
                - chart.planets["Ketu"].chain.longitude)
        assert min(d, 360 - d) == pytest.approx(180.0, abs=1e-6)


# ------------------------------------------------------------- significators
class TestSignificators:
    def test_every_house_has_an_owner(self):
        chart = build_chart(NANGAL)
        for h in house_significators(chart):
            assert h.level_d, f"house {h.house} has no owner"

    def test_nodes_own_nothing(self):
        chart = build_chart(NANGAL)
        own = chart.ownerships()
        assert "Rahu" not in own and "Ketu" not in own

    def test_occupants_total_nine(self):
        chart = build_chart(NANGAL)
        assert sum(len(v) for v in chart.occupants().values()) == 9

    def test_own_star_gives_positional_status(self):
        sig = planet_significations(build_chart(NANGAL))
        assert sig["Sun"].in_own_star
        assert sig["Sun"].positional_status

    def test_node_borrows_sign_lord_houses(self):
        chart = build_chart(NANGAL)
        sig = planet_significations(chart)
        ketu_sign_lord = chart.planets["Ketu"].chain.sign_lord
        borrowed = set(chart.ownerships().get(ketu_sign_lord, []))
        assert borrowed <= set(sig["Ketu"].all_houses())


# ------------------------------------------------------------- sensitivity
class TestSensitivity:
    def test_known_tight_cusps_flagged_critical(self):
        """Lagna sits 14' from the edge of Mars' sub -- houses 1 and 7 must
        require the exact recorded minute."""
        rep = scan(NANGAL)
        assert 1 in rep.critical_houses
        assert 7 in rep.critical_houses

    def test_wide_cusps_not_flagged(self):
        """Not everything is critical -- if it were, the panel would be noise."""
        rep = scan(NANGAL)
        assert len(rep.critical_houses) < 12
        assert any(c.holds_across_window for c in rep.cusps)

    def test_zero_window_holds_everything(self):
        rep = scan(NANGAL, window_minutes=0.0)
        assert all(c.holds_across_window for c in rep.cusps)

    def test_margin_and_flip_are_consistent(self):
        rep = scan(NANGAL)
        for c in rep.cusps:
            assert (c.flips_at_minutes is None) == c.holds_across_window
            if c.flips_at_minutes is not None:
                assert c.holds_to_minutes < c.flips_at_minutes
                assert len(c.variants) > 1
            else:
                assert c.variants == (c.base_sub_lord,)

    def test_base_sub_lord_matches_chart(self):
        rep = scan(NANGAL)
        chart = build_chart(NANGAL)
        for c in rep.cusps:
            assert c.base_sub_lord == chart.cuspal_sub_lord(c.house)

    def test_wide_window_makes_everything_move(self):
        """Documents the finding that motivated the margin design: at +/-5 min
        every cusp changes, so a binary verdict there is uninformative."""
        rep = scan(NANGAL, window_minutes=5.0, step_minutes=0.5)
        assert all(not c.holds_across_window for c in rep.cusps)

    def test_headline_is_non_empty(self):
        assert scan(NANGAL).headline().strip()

    def test_bad_step_rejected(self):
        with pytest.raises(ValueError):
            scan(NANGAL, step_minutes=0.0)


# ----------------------------------------------------------------- golden
class TestGolden:
    def test_matches_validated_snapshot(self):
        expected = json.loads(GOLDEN.read_text())
        assert snapshot(NANGAL) == expected

    def test_vp291_differs_from_classic(self):
        """One arc-minute of ayanamsa must be able to move a sub lord.
        If this ever passes as 'identical', the ayanamsa is not being applied."""
        vp = BirthInput(**{**{f: getattr(NANGAL, f) for f in
                              ("year", "month", "day", "hour", "minute",
                               "tz_offset_hours", "latitude", "longitude")},
                           "ayanamsa": KPAyanamsa.VP291})
        a = {p["name"]: p["sub"] for p in snapshot(NANGAL)["planets"]}
        b = {p["name"]: p["sub"] for p in snapshot(vp)["planets"]}
        assert a != b


class TestModeTracking:
    def test_nested_guards_restore_predecessor_not_default(self):
        from kp.context import current_mode
        from kp import set_mode
        set_mode(swe.SIDM_RAMAN)
        try:
            with sidereal_mode(KPAyanamsa.CLASSIC):
                assert current_mode() == int(KPAyanamsa.CLASSIC)
                with sidereal_mode(KPAyanamsa.VP291):
                    assert current_mode() == int(KPAyanamsa.VP291)
                assert current_mode() == int(KPAyanamsa.CLASSIC)
            assert current_mode() == swe.SIDM_RAMAN
        finally:
            set_mode(DEFAULT_SID_MODE)

    def test_restores_non_lahiri_host_mode(self):
        """If the host engine uses something other than Lahiri, KP must hand
        that back -- not a hardcoded default."""
        from kp.context import current_mode
        from kp import set_mode
        set_mode(swe.SIDM_RAMAN)
        try:
            build_chart(NANGAL)
            assert current_mode() == swe.SIDM_RAMAN
        finally:
            set_mode(DEFAULT_SID_MODE)

    def test_configure_default_is_respected(self):
        from kp.context import configure_default, current_mode
        import kp.context as ctx
        original = ctx.DEFAULT_SID_MODE
        try:
            configure_default(swe.SIDM_RAMAN)
            assert current_mode() == swe.SIDM_RAMAN
        finally:
            configure_default(original)


class TestNoImportSideEffects:
    def test_importing_kp_does_not_change_sid_mode(self):
        """The host may set its mode before importing kp. Import must not
        clobber it."""
        import subprocess
        import sys as _s
        code = (
            "import swisseph as swe;"
            "swe.set_sid_mode(swe.SIDM_RAMAN);"
            "a=swe.get_ayanamsa_ut(2448516.0);"
            "import kp;"
            "b=swe.get_ayanamsa_ut(2448516.0);"
            "print('SAME' if a==b else 'CLOBBERED')"
        )
        out = subprocess.run([_s.executable, "-c", code],
                             cwd=str(pathlib.Path(__file__).resolve().parents[1]),
                             capture_output=True, text=True)
        assert "SAME" in out.stdout, out.stdout + out.stderr
