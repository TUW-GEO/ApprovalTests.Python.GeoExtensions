from datetime import datetime

import pytest
from approvaltests.scrubbers import scrub_all_dates

from factories import make_raster_at
from pytest_approvaltests_geo.compare_geo_tiffs import CompareGeoTiffs
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse


@pytest.fixture
def comparator():
    return CompareGeoTiffs()


def test_compare_identical_geo_tiffs(comparator, tmp_path):
    geo_tif = make_raster_at([[42]], tmp_path / "geo_tif.tif", dict(some='tag'))
    assert comparator.compare(geo_tif.as_posix(), geo_tif.as_posix())


def test_compare_geo_tiffs_with_differing_tags(comparator, tmp_path):
    received = make_raster_at([[42]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_raster_at([[42]], tmp_path / "approved.tif", dict(some='other'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_tiffs_with_differing_pixels(comparator, tmp_path):
    received = make_raster_at([[42]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_raster_at([[21]], tmp_path / "approved.tif", dict(some='tag'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_tiffs_applies_scrubbers_to_tags(tmp_path):
    scrubbing_comparator = CompareGeoTiffs(make_scrubber_recurse(scrub_all_dates))
    received = make_raster_at([[42]], tmp_path / "received.tif",
                              dict(some=datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S")))
    approved = make_raster_at([[42]], tmp_path / "approved.tif",
                              dict(some=datetime(2022, 1, 2).strftime("%Y-%m-%d %H:%M:%S")))
    assert scrubbing_comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_tiffs_floats_with_tolerances(tmp_path):
    tolerant_comparator = CompareGeoTiffs(float_tolerance=Tolerance(rel=0.008, abs=0.0021))
    received = make_raster_at([[-1.01]], tmp_path / "received.tif")
    approved = make_raster_at([[-1.0]], tmp_path / "approved.tif")
    assert tolerant_comparator.compare(received.as_posix(), approved.as_posix())
