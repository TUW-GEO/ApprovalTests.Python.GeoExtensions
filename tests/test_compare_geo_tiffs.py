from datetime import datetime

import pytest
from approval_utilities.utils import to_json
from approvaltests.scrubbers import scrub_all_dates

from factories import make_raster_at
from pytest_approvaltests_geo.compare_geo_tiffs import CompareGeoTiffs


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
    scrubbing_comparator = CompareGeoTiffs(lambda tags: scrub_all_dates(to_json(tags)))
    received = make_raster_at([[42]], tmp_path / "received.tif",
                              dict(some=datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S")))
    approved = make_raster_at([[42]], tmp_path / "approved.tif",
                              dict(some=datetime(2022, 1, 2).strftime("%Y-%m-%d %H:%M:%S")))
    assert scrubbing_comparator.compare(received.as_posix(), approved.as_posix())
