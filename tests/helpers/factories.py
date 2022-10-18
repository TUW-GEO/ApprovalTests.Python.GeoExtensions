from pathlib import Path

import rioxarray  # noqa # pylint: disable=unused-import

from pytest_approvaltests_geo.factories import make_raster


def make_raster_at(values, file_path: Path, tags=None) -> Path:
    array = make_raster(values)
    array.rio.to_raster(file_path, tags=tags)
    return file_path
