from datetime import datetime

import pytest
from approval_utilities.utils import to_json
from approvaltests.scrubbers import scrub_all_dates

from factories import make_raster_at
from pytest_approvaltests_geo.report_geo_tiffs import ReportGeoTiffs


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
