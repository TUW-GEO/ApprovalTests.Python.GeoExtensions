from pathlib import Path
from typing import Tuple, Dict

import rasterio
import rioxarray
from xarray import DataArray


def read_array_and_tags(file_path: Path) -> Tuple[DataArray, Dict]:
    with rasterio.open(file_path) as rds:
        t = rds.tags()
        a = rioxarray.open_rasterio(rds)
    return a, t
