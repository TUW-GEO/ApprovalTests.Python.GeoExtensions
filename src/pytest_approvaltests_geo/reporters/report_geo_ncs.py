from pathlib import Path

import numpy as np
from approvaltests import Reporter
from approvaltests.reporters import get_command_text
from xarray import Dataset

from pytest_approvaltests_geo.differs.differ_of_geo_ncs import DifferOfGeoNcs
from pytest_approvaltests_geo.differs.difference import print_diffs


class ReportGeoNcs(Reporter, DifferOfGeoNcs):
    def report(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)

        if not approved_path.is_file():
            self._create_empty_geo_nc(approved_path)

        diffs = self.diffs(received_path, approved_path)
        if len(diffs) > 0:
            print_diffs(diffs)
            print(f"To approve run:\n {get_command_text(received_path.as_posix(), approved_path.as_posix())}")

        return True

    @staticmethod
    def _create_empty_geo_nc(path: Path):
        Dataset({'empty': (("x", "y"), np.empty((1, 1)))}).to_netcdf(path)
