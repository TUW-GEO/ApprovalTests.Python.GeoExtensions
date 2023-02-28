from datetime import datetime

import pytest
from approvaltests.scrubbers import create_regex_scrubber
from xarray import DataArray

from factories import make_raster_at
from pytest_approvaltests_geo.comparators.compare_geo_tiffs import CompareGeoTiffs
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse, make_scrubber_sequential


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


def test_compare_geo_tiffs_with_differing_array_attrs(comparator, tmp_path):
    received = make_raster_at([[42]], tmp_path / "received.tif", array_attrs=dict(some='tag'))
    approved = make_raster_at([[42]], tmp_path / "approved.tif", array_attrs=dict(some='other'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_tiffs_with_differing_coord_attrs(comparator, tmp_path):
    received = make_raster_at([[42]], tmp_path / "received.tif", coords=dict(
        band=[1], x=[0], y=[0], spatial_ref=DataArray(0, attrs={'GeoTransform': "-0.5 1.0 0.0 -0.5 0.0 1.0"})
    ))
    approved = make_raster_at([[42]], tmp_path / "approved.tif", coords=dict(
        band=[1], x=[0], y=[0], spatial_ref=DataArray(0, attrs={'GeoTransform': "-0.5 10.0 0.0 -0.5 0.0 10.0"})
    ))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_tiffs_with_differing_pixels(comparator, tmp_path):
    received = make_raster_at([[42]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_raster_at([[21]], tmp_path / "approved.tif", dict(some='tag'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_tiffs_applies_scrubbers_to_meta_data(tmp_path):
    date_scrubber = create_regex_scrubber(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}", lambda t: f"<date{t}>")
    scrubbing_comparator = CompareGeoTiffs(make_scrubber_recurse(date_scrubber))
    date_old = datetime(2022, 1, 1).strftime("%Y-%m-%dT%H-%M-%S")
    date_new = datetime(2022, 1, 2).strftime("%Y-%m-%dT%H-%M-%S")
    received = make_raster_at([[42]], tmp_path / "received.tif", dict(some=date_old), {date_old: 42})
    approved = make_raster_at([[42]], tmp_path / "approved.tif", dict(some=date_new), {date_new: 42})
    assert scrubbing_comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_tiffs_floats_with_tolerances(tmp_path):
    tolerant_comparator = CompareGeoTiffs(float_tolerance=Tolerance(rel=0.008, abs=0.0021))
    received = make_raster_at([[-1.01]], tmp_path / "received.tif")
    approved = make_raster_at([[-1.0]], tmp_path / "approved.tif")
    assert tolerant_comparator.compare(received.as_posix(), approved.as_posix())
