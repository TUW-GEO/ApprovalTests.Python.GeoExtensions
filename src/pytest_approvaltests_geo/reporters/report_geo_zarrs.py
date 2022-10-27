from pathlib import Path

import numpy as np
from approvaltests import Reporter
from xarray import Dataset

from pytest_approvaltests_geo.differs.differ_of_geo_zarrs import DifferOfGeoZarrs
from pytest_approvaltests_geo.differs.difference import print_diffs


class ReportGeoZarrs(Reporter, DifferOfGeoZarrs):
    def report(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)

        if not approved_path.exists():
            self._create_empty_ds(approved_path)

        diffs = self.diffs(received_path, approved_path)
        if len(diffs) > 0:
            print_diffs(diffs)
            print(f"To approve run:\nrm -rf {approved_path} && mv -f {received_path} {approved_path}")

        return True

    @staticmethod
    def _create_empty_ds(path: Path):
        Dataset({'empty': (("x", "y"), np.empty((1, 1)))}).to_zarr(path)
