from datetime import datetime

import pytest
from approvaltests.scrubbers import create_regex_scrubber

from factories import make_zarr_at
from pytest_approvaltests_geo.compare_geo_zarrs import CompareGeoZarrs
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse


@pytest.fixture
def comparator():
    return CompareGeoZarrs()


def test_compare_identical_geo_zarrs(comparator, tmp_path):
    geo_tif = make_zarr_at([[42]], tmp_path / "geo_tif.zarr", dict(some='tag'))
    assert comparator.compare(geo_tif.as_posix(), geo_tif.as_posix())


def test_compare_geo_zarrs_with_differing_attrs(comparator, tmp_path):
    received = make_zarr_at([[42]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_zarr_at([[42]], tmp_path / "approved.tif", dict(some='other'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_zarrs_with_differing_pixels(comparator, tmp_path):
    received = make_zarr_at([[42]], tmp_path / "received.tif", dict(some='tag'))
    approved = make_zarr_at([[21]], tmp_path / "approved.tif", dict(some='tag'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_zarrs_tiffs_applies_scrubbers_to_tags(tmp_path):
    date_scrubber = create_regex_scrubber(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}", lambda t: f"<date{t}>")
    scrubbing_comparator = CompareGeoZarrs(make_scrubber_recurse(date_scrubber))
    date_old = datetime(2022, 1, 1).strftime("%Y-%m-%dT%H-%M-%S")
    date_new = datetime(2022, 1, 2).strftime("%Y-%m-%dT%H-%M-%S")
    received = make_zarr_at([[42]], tmp_path / "received.tif", {date_old: 42}, dict(some=date_old))
    approved = make_zarr_at([[42]], tmp_path / "approved.tif", {date_new: 42}, dict(some=date_new))
    assert scrubbing_comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_zarrs_floats_with_tolerances(tmp_path):
    tolerant_comparator = CompareGeoZarrs(float_tolerance=Tolerance(rel=0.008, abs=0.0021))
    received = make_zarr_at([[-1.01]], tmp_path / "received.tif")
    approved = make_zarr_at([[-1.0]], tmp_path / "approved.tif")
    assert tolerant_comparator.compare(received.as_posix(), approved.as_posix())
