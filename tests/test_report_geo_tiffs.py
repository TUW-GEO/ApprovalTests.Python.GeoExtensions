import pytest

from factories import make_raster_at
from pytest_approvaltests_geo.report_geo_tiffs import ReportGeoTiffs


@pytest.fixture
def reporter():
    return ReportGeoTiffs()


def test_identical_geo_tiffs_report_nothing(reporter, tmp_path, capsys):
    geo_tif = make_raster_at([[42]], tmp_path / "geo_tif.tif", dict(some='tag'))
    assert reporter.report(geo_tif.as_posix(), geo_tif.as_posix())
    assert capsys.readouterr().out == ""
