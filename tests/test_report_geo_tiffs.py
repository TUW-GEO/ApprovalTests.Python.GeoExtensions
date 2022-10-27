from datetime import datetime

import numpy as np
import pytest
from approvaltests.scrubbers import create_regex_scrubber

from factories import make_raster_at
from pytest_approvaltests_geo.reporters.report_geo_tiffs import ReportGeoTiffs
from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse

PIXEL_DIFF_REPORT_PATTERN = "[data][band=1"


@pytest.fixture
def reporter():
    return ReportGeoTiffs()


def test_identical_geo_tiffs_report_nothing(reporter, tmp_path, capsys):
    geo_tif = make_raster_at([[42]], tmp_path / "geo_tif.tif", dict(some='tag'))
    assert reporter.report(geo_tif.as_posix(), geo_tif.as_posix())
    assert capsys.readouterr().out == ""


def test_report_pixel_difference_statistics(reporter, tmp_path, capsys):
    received = make_raster_at([[0, 0], [0, 0]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_raster_at([[2, 4], [-2, 1]], tmp_path / "approved.tif", dict(some='tag'))
    assert reporter.report(received.as_posix(), approved.as_posix())
    assert "min=1, max=4, mean=2.25, median=2" in capsys.readouterr().out


def test_report_meta_data_differences(reporter, tmp_path, capsys):
    received = make_raster_at([[42]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_raster_at([[42]], tmp_path / "approved.tif", dict(some='other'))
    assert reporter.report(received.as_posix(), approved.as_posix())
    output = capsys.readouterr().out
    assert '+    "some": "tag"' in output and '-    "some": "other"' in output


def test_report_scrubbed_data(tmp_path, capsys):
    date_scrubber = create_regex_scrubber(
        r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}", lambda t: f"<date{t}>"
    )
    scrubbing_reporter = ReportGeoTiffs(make_scrubber_recurse(date_scrubber))
    received = make_raster_at([[0, 0], [0, 0]], tmp_path / "received.tif",
                              {"some": datetime(2022, 1, 1).strftime("%Y-%m-%dT%H-%M-%S"),
                               datetime(2022, 2, 1).strftime("%Y-%m-%dT%H-%M-%S"): 42})
    approved = make_raster_at([[2, 4], [-2, 1]], tmp_path / "approved.tif",
                              {"other": datetime(2022, 1, 1).strftime("%Y-%m-%dT%H-%M-%S"),
                               datetime(2022, 2, 1).strftime("%Y-%m-%dT%H-%M-%S"): 21})
    assert scrubbing_reporter.report(received.as_posix(), approved.as_posix())
    output = capsys.readouterr().out
    assert '+    "some": "<date0>"' in output and '-    "other": "<date0>"' in output
    assert '+    "<date0>": "42"' in output and '-    "<date0>": "21"' in output


def test_report_has_maximum_length_when_reporting_differing_pixels(reporter, tmp_path, capsys):
    received = make_raster_at(np.zeros((100, 100)), tmp_path / "received.tif", dict(some='tag'))
    approved = make_raster_at(np.ones((100, 100)), tmp_path / "approved.tif", dict(some='tag'))
    assert reporter.report(received.as_posix(), approved.as_posix())
    diff_pixel_lines = [line for line in capsys.readouterr().out.splitlines() if PIXEL_DIFF_REPORT_PATTERN in line]
    assert len(diff_pixel_lines) < 10
