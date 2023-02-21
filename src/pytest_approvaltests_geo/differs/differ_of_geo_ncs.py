from typing import Optional

import xarray as xr

from pytest_approvaltests_geo.differs.differ_of_geo_dataset import DifferOfGeoDataset
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.scrubbers import RecursiveScrubber, identity_recursive_scrubber


class DifferOfGeoNcs(DifferOfGeoDataset):
    def __init__(self, recursive_scrubber: Optional[RecursiveScrubber] = None,
                 float_tolerance: Optional[Tolerance] = None):
        super().__init__(xr.open_dataset,
                         recursive_scrubber or identity_recursive_scrubber,
                         float_tolerance or Tolerance())
