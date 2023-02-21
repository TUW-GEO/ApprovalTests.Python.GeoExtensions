from datetime import datetime

import pytest
from approvaltests.scrubbers import create_regex_scrubber
from xarray import DataArray

from factories import make_nc_at
from pytest_approvaltests_geo.comparators.compare_geo_ncs import CompareGeoNcs
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse


@pytest.fixture
def comparator():
    return CompareGeoNcs()


def test_compare_identical_geo_ncs(comparator, tmp_path):
    geo_nc = make_nc_at([[42]], tmp_path / "geo_nc.nc", dict(some='tag'))
    assert comparator.compare(geo_nc.as_posix(), geo_nc.as_posix())


def test_compare_geo_ncs_with_differing_attrs(comparator, tmp_path):
    received = make_nc_at([[42]], tmp_path / "received.nc", dict(some='tag'))
    approved = make_nc_at([[42]], tmp_path / "approved.nc", dict(some='other'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_ncs_with_differing_data_var_attrs(comparator, tmp_path):
    received = make_nc_at([[42]], tmp_path / "received.nc", array_attrs=dict(some='tag'))
    approved = make_nc_at([[42]], tmp_path / "approved.nc", array_attrs=dict(some='other'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_ncs_with_differing_coord_attrs(comparator, tmp_path):
    received = make_nc_at([[42]], tmp_path / "received.nc", coords=dict(
        band=[1], x=[0], y=[0], spatial_ref=DataArray(0, attrs=dict(some='tag'))
    ))
    approved = make_nc_at([[42]], tmp_path / "approved.nc", coords=dict(
        band=[1], x=[0], y=[0], spatial_ref=DataArray(0, attrs=dict(some='other'))
    ))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_ncs_with_differing_pixels(comparator, tmp_path):
    received = make_nc_at([[42]], tmp_path / "received.nc", dict(some='tag'))
    approved = make_nc_at([[21]], tmp_path / "approved.nc", dict(some='tag'))
    assert not comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_ncs_applies_scrubbers_to_all_meta_data(tmp_path):
    date_scrubber = create_regex_scrubber(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}", lambda t: f"<date{t}>")
    scrubbing_comparator = CompareGeoNcs(make_scrubber_recurse(date_scrubber))
    date_old = datetime(2022, 1, 1).strftime("%Y-%m-%dT%H-%M-%S")
    date_new = datetime(2022, 1, 2).strftime("%Y-%m-%dT%H-%M-%S")
    received = make_nc_at([[42]], tmp_path / "received.nc", {date_old: 42}, dict(some=date_old), coords=dict(
        band=[1], x=[0], y=[0], spatial_ref=DataArray(0, attrs=dict(some=date_old))
    ))
    approved = make_nc_at([[42]], tmp_path / "approved.nc", {date_new: 42}, dict(some=date_new), coords=dict(
        band=[1], x=[0], y=[0], spatial_ref=DataArray(0, attrs=dict(some=date_new))
    ))
    assert scrubbing_comparator.compare(received.as_posix(), approved.as_posix())


def test_compare_geo_ncs_floats_with_tolerances(tmp_path):
    tolerant_comparator = CompareGeoNcs(float_tolerance=Tolerance(rel=0.008, abs=0.0021))
    received = make_nc_at([[-1.01]], tmp_path / "received.nc")
    approved = make_nc_at([[-1.0]], tmp_path / "approved.nc")
    assert tolerant_comparator.compare(received.as_posix(), approved.as_posix())
