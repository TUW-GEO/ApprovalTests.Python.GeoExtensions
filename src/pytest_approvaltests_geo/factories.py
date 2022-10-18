import numpy as np
from xarray import DataArray


def make_raster(values):
    values = _ensure_band_dimension(values)
    array = DataArray(values, dims=['band', 'y', 'x'], coords=(dict(band=np.arange(values.shape[0]) + 1,
                                                                    y=np.arange(values.shape[1]),
                                                                    x=np.arange(values.shape[2]),
                                                                    spatial_ref=0)))
    return array


def _ensure_band_dimension(expected):
    expected = np.array(expected)
    if expected.ndim == 2:
        expected = expected[np.newaxis, ...]
    return expected
