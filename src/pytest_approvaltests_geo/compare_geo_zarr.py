import shutil
from pathlib import Path
from typing import Dict, Optional

import xarray as xr
from approvaltests.core import Comparator
from recursive_diff import recursive_diff

from pytest_approvaltests_geo import RecursiveScrubber
from pytest_approvaltests_geo.float_utils import Tolerance


def _identity_tags_scrubber(tags: Dict) -> Dict:
    return tags


class CompareGeoZarr(Comparator):
    def __init__(self, tags_scrubber: Optional[RecursiveScrubber] = None, float_tolerance: Optional[Tolerance] = None):
        self._tags_scrubber = tags_scrubber or _identity_tags_scrubber
        self._float_tolerance = float_tolerance or Tolerance()

    def compare(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)
        if not received_path.exists() or not approved_path.exists():
            return False

        with xr.open_zarr(received_path) as received_ds, xr.open_zarr(approved_path) as approved_ds:
            received_ds.attrs = self._tags_scrubber(received_ds.attrs)
            approved_ds.attrs = self._tags_scrubber(approved_ds.attrs)
            for name in received_ds.data_vars:
                received_ds[name].attrs = self._tags_scrubber(received_ds[name].attrs)
            for name in approved_ds.data_vars:
                approved_ds[name].attrs = self._tags_scrubber(approved_ds[name].attrs)

            diffs = list(recursive_diff(received_ds, approved_ds, **self._float_tolerance.to_kwargs()))
            is_identical = len(diffs) == 0
            if is_identical:
                shutil.rmtree(received_path)
                received_path.touch()  # TODO: fix so approval tests has something to delete
            return is_identical
