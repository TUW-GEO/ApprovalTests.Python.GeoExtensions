from contextlib import contextmanager
from pathlib import Path
from typing import Tuple, Dict

import rasterio
import rioxarray
from xarray import DataArray


@contextmanager
def read_array_and_tags(file_path: Path) -> Tuple[DataArray, Dict]:
    try:
        with rasterio.open(file_path) as rds:
            t = rds.tags()
            a = rioxarray.open_rasterio(rds)
        yield a, t
    finally:
        a.close()
