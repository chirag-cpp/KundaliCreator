"""Cross-engine isolation.

The KP package must not perturb the Lahiri engine. These tests build a full
Kundali report, run KP work in between, and assert the report is byte-identical.
"""
import pathlib
import sys

import pytest
import swisseph as swe

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from generate_kundali import build_report
from kp import BirthInput, build_chart, scan

CASE = dict(dob="1991-09-16", time="22:50", lat=31.3880, lon=76.3773,
            tz="Asia/Kolkata", place_label="Nangal")
KP_BIRTH = BirthInput.from_zone(CASE["dob"], CASE["time"], CASE["lat"],
                                CASE["lon"], CASE["tz"])


def test_report_is_identical_before_and_after_kp():
    before = build_report(**CASE)
    build_chart(KP_BIRTH)
    after = build_report(**CASE)
    assert before == after


def test_report_survives_a_sensitivity_scan():
    """The scan builds 9 charts in a row -- the heaviest KP workload."""
    before = build_report(**CASE)
    scan(KP_BIRTH)
    assert build_report(**CASE) == before


def test_report_survives_kp_raising():
    before = build_report(**CASE)
    with pytest.raises(Exception):
        BirthInput(1991, 9, 16, 22, 50, 5.5, 80.0, 25.0)   # polar guard
    try:
        build_chart(BirthInput(1991, 9, 16, 22, 50, 5.5, 65.9, 25.0))
    except Exception:
        pass
    assert build_report(**CASE) == before


def test_ayanamsa_guard_still_passes_after_kp():
    from core import ayanamsa_check
    build_chart(KP_BIRTH)
    name, val = ayanamsa_check(swe.julday(1991, 9, 16, 17.333))
    assert 23.0 < val < 24.5


def test_interleaved_many_times():
    base = build_report(**CASE)
    for _ in range(3):
        build_chart(KP_BIRTH)
        assert build_report(**CASE) == base


def test_two_engines_disagree_on_houses_as_expected():
    """Sanity: they are genuinely different systems, not accidentally aliased."""
    from core import Chart
    ch = Chart(CASE["dob"], CASE["time"], CASE["lat"], CASE["lon"], CASE["tz"])
    kp = build_chart(KP_BIRTH)
    assert abs(ch.ayanamsa - kp.ayanamsa_deg) > 0.05      # Lahiri vs KP
