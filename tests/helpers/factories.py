from pathlib import Path

import rioxarray  # noqa # pylint: disable=unused-import
from xarray import Dataset

from pytest_approvaltests_geo.factories import make_raster


def make_raster_at(values, file_path: Path, tags=None, array_attrs=None, coords=None) -> Path:
    array = make_raster(values, coords=coords, attrs=array_attrs)
    array.rio.to_raster(file_path, tags=tags)
    return file_path


def make_zarr_at(values, file_path: Path, ds_attrs=None, array_attrs=None, coords=None) -> Path:
    array = make_raster(values, coords=coords, attrs=array_attrs)
    ds = Dataset(dict(var_name=array))
    ds.attrs = ds_attrs or {}
    ds.to_zarr(file_path)
    return file_path

def make_nc_at(values, file_path: Path, ds_attrs=None, array_attrs=None, coords=None) -> Path:
    array = make_raster(values, coords=coords, attrs=array_attrs)
    ds = Dataset(dict(var_name=array))
    ds.attrs = ds_attrs or {}
    ds.to_netcdf(file_path)
    return file_path