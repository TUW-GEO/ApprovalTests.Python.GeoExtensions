from pathlib import Path

import numpy as np
import rioxarray    # noqa # pylint: disable=unused-import

from xarray import DataArray


def make_raster_at(values, file_path: Path, tags=None) -> Path:
    values = _ensure_band_dimension(values)
    array = DataArray(values, dims=['band', 'y', 'x'], coords=(dict(band=np.arange(values.shape[0]) + 1,
                                                                    y=np.arange(values.shape[1]),
                                                                    x=np.arange(values.shape[2]),
                                                                    spatial_ref=0)))
    array.rio.to_raster(file_path, tags=tags, compress='ZSTD')
    return file_path


def _ensure_band_dimension(expected):
    expected = np.array(expected)
    if expected.ndim == 2:
        expected = expected[np.newaxis, ...]
    return expected
