from pathlib import Path
from typing import Sequence, Optional

import xarray as xr
from recursive_diff import recursive_diff
from xarray.core import formatting

from pytest_approvaltests_geo.difference import DiffType, Difference, calculate_pixel_diff_stats, shorten_pixel_diffs
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.scrubbers import RecursiveScrubber, identity_recursive_scrubber


class DifferOfGeoZarrs:
    def __init__(self, recursive_scrubber: Optional[RecursiveScrubber] = None,
                 float_tolerance: Optional[Tolerance] = None):
        self._recursive_scrubber = recursive_scrubber or identity_recursive_scrubber
        self._float_tolerance = float_tolerance or Tolerance()

    def diffs(self, received_path: Path, approved_path: Path) -> Sequence[Difference]:
        diffs = []
        with xr.open_zarr(received_path) as received_ds, xr.open_zarr(approved_path) as approved_ds:
            received_ds.attrs = self._recursive_scrubber(received_ds.attrs)
            approved_ds.attrs = self._recursive_scrubber(approved_ds.attrs)
            for name in received_ds.data_vars:
                received_ds[name].attrs = self._recursive_scrubber(received_ds[name].attrs)
            for name in approved_ds.data_vars:
                approved_ds[name].attrs = self._recursive_scrubber(approved_ds[name].attrs)

            diff_px = list(recursive_diff(approved_ds, received_ds, **self._float_tolerance.to_kwargs()))
            if len(diff_px) > 0:
                diff_stats = '\n'.join([str(calculate_pixel_diff_stats(received_ds[name], approved_ds[name]))
                                        for name in approved_ds.data_vars if name in received_ds.data_vars])
                diffs.append(Difference(diff_stats, DiffType.PIXEL_STATS))
                diff_px = shorten_pixel_diffs(diff_px)
                diffs.append(Difference('\n'.join(diff_px), DiffType.PIXEL))
                diff_ds = formatting.diff_dataset_repr(approved_ds, received_ds, "identical")
                diffs.append(Difference(diff_ds, DiffType.DATASET))

        return diffs
