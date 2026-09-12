"""End-to-end page tests using Streamlit's own test harness.

A boot test (does the server return 200?) does not execute page code. These
drive the actual widgets, which is what would have caught the
UnserializableReturnValueError from caching a KPChart.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

APP = str(ROOT / "app.py")


def _run(timeout=90):
    at = AppTest.from_file(APP, default_timeout=timeout)
    at.run()
    return at


def test_default_page_has_no_exception():
    assert not _run().exception


def test_kp_page_renders_a_chart():
    at = _run()
    at.radio[0].set_value("KP chart").run()
    # switch the place widget to coordinate entry, then fill it in
    at.radio[1].set_value("Enter coordinates").run()
    at.number_input(key="kp_lat").set_value(31.3880)
    at.number_input(key="kp_lon").set_value(76.3773)
    at.text_input(key="kp_tz").set_value("Asia/Kolkata")
    at.run()
    assert not at.exception, at.exception
    assert at.dataframe, "KP page rendered no tables"


def test_numerology_page_has_no_exception():
    at = _run()
    at.radio[0].set_value("Vedic numerology").run()
    assert not at.exception, at.exception
