from typing import Optional

import xarray as xr

from pytest_approvaltests_geo.differs.differ_of_geo_dataset import DifferOfGeoDataset
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.scrubbers import RecursiveScrubber, identity_recursive_scrubber, SequenceScrubber, \
    identity_sequence_scrubber


class DifferOfGeoZarrs(DifferOfGeoDataset):
    def __init__(self, tags_scrubber: Optional[RecursiveScrubber] = None,
                 coords_scrubber: Optional[SequenceScrubber] = None,
                 float_tolerance: Optional[Tolerance] = None):
        super().__init__(xr.open_zarr,
                         tags_scrubber or identity_recursive_scrubber,
                         coords_scrubber or identity_sequence_scrubber,
                         float_tolerance or Tolerance())
