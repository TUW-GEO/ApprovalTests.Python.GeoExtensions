from pathlib import Path

from approvaltests import Reporter
from approvaltests.reporters import get_command_text
from xarray import DataArray

from pytest_approvaltests_geo.differ_of_geo_tiffs import DifferOfGeoTiffs, DiffType


class ReportGeoTiffs(Reporter, DifferOfGeoTiffs):
    DIFF_TYPE_PREFIXES = {
        DiffType.TAGS: "Differences in meta data:\n",
        DiffType.PIXEL_STATS: "Differences in pixel data:\n",
    }

    def report(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)

        if not approved_path.is_file():
            self._create_empty_geotiff(approved_path)

        diffs = self.diffs(received_path, approved_path)
        if len(diffs) > 0:
            for diff in diffs:
                print(f"{ReportGeoTiffs.DIFF_TYPE_PREFIXES[diff.type]}{diff.description}")
            print(f"To approve run:\n {get_command_text(received_path.as_posix(), approved_path.as_posix())}")

        return True

    @staticmethod
    def _create_empty_geotiff(path: Path):
        DataArray([[0]], dims=['y', 'x']).rio.to_raster(path)
