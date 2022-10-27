import numpy as np
from xarray import DataArray


def make_raster(values, attrs=None, coords=None):
    values = _ensure_band_dimension(values)
    coords = coords or dict(band=np.arange(values.shape[0]) + 1,
                            y=np.arange(values.shape[1]),
                            x=np.arange(values.shape[2]),
                            spatial_ref=0)
    array = DataArray(values, dims=['band', 'y', 'x'], coords=coords, attrs=attrs)
    return array


def _ensure_band_dimension(expected):
    expected = np.array(expected)
    if expected.ndim == 2:
        expected = expected[np.newaxis, ...]
    return expected
