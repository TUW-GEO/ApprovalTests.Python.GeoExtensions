from datetime import datetime

import pytest
from approvaltests.scrubbers import create_regex_scrubber

from factories import make_zarr_at
from pytest_approvaltests_geo.report_geo_zarrs import ReportGeoZarrs
from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse


@pytest.fixture
def reporter():
    return ReportGeoZarrs()


def test_identical_geo_tiffs_report_nothing(reporter, tmp_path, capsys):
    geo_tif = make_zarr_at([[42]], tmp_path / "geo_tif.tif", dict(some='tag'))
    assert reporter.report(geo_tif.as_posix(), geo_tif.as_posix())
    assert capsys.readouterr().out == ""


def test_report_pixel_differences_and_statistics(reporter, tmp_path, capsys):
    received = make_zarr_at([[0, 0], [0, 0]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_zarr_at([[2, 4], [-2, 1]], tmp_path / "approved.tif", dict(some='tag'))
    assert reporter.report(received.as_posix(), approved.as_posix())
    std_out = capsys.readouterr().out
    assert "min=1, max=4, mean=2.25, median=2" in std_out


def test_report_meta_data_differences(reporter, tmp_path, capsys):
    received = make_zarr_at([[42]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_zarr_at([[42]], tmp_path / "approved.tif", dict(some='other'))
    assert reporter.report(received.as_posix(), approved.as_posix())
    output = capsys.readouterr().out
    assert 'L   some: tag' in output and 'R   some: other' in output


def test_report_scrubbed_data(tmp_path, capsys):
    date_scrubber = create_regex_scrubber(
        r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}", lambda t: f"<date{t}>"
    )
    scrubbing_reporter = ReportGeoZarrs(make_scrubber_recurse(date_scrubber))
    date_old = datetime(2022, 1, 1).strftime("%Y-%m-%dT%H-%M-%S")
    date_new = datetime(2022, 2, 1).strftime("%Y-%m-%dT%H-%M-%S")
    received = make_zarr_at([[0, 0], [0, 0]], tmp_path / "received.tif",
                            {"some": date_old}, {date_new: 42})
    approved = make_zarr_at([[2, 4], [-2, 1]], tmp_path / "approved.tif",
                            {"other": date_old}, {date_new: 21})
    assert scrubbing_reporter.report(received.as_posix(), approved.as_posix())
    output = capsys.readouterr().out
    assert 'other: <date0>' in output and '<date0>: 42' in output
    assert 'some: <date0>' in output and '<date0>: 21' in output
