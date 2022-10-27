from pathlib import Path
from typing import Sequence, Optional

import xarray as xr

from pytest_approvaltests_geo.difference import DiffType, Difference, calculate_pixel_diff_stats
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
            received_data_vars = set(received_ds.data_vars)
            approved_data_vars = set(approved_ds.data_vars)
            received_coords = set(received_ds.coords)
            approved_coords = set(approved_ds.coords)
            for name in received_data_vars:
                received_ds[name].attrs = self._recursive_scrubber(received_ds[name].attrs)
            for name in approved_data_vars:
                approved_ds[name].attrs = self._recursive_scrubber(approved_ds[name].attrs)
            for name in received_coords:
                received_ds[name].attrs = self._recursive_scrubber(received_ds[name].attrs)
            for name in approved_coords:
                approved_ds[name].attrs = self._recursive_scrubber(approved_ds[name].attrs)

            diff_attrs = xr.testing.formatting.diff_attrs_repr(received_ds.attrs, approved_ds.attrs, 'identical')
            if diff_attrs:
                diffs.append(Difference(diff_attrs, DiffType.TAGS))

            common_data_vars = received_data_vars & approved_data_vars
            common_coords = received_coords & approved_coords
            common_sub_arrays = list(common_data_vars) + list(common_coords)
            for name in common_sub_arrays:
                d = xr.testing.formatting.diff_attrs_repr(received_ds[name].attrs, approved_ds[name].attrs, 'identical')
                if d:
                    diffs.append(Difference(d, DiffType.TAGS))

            try:
                xr.testing.assert_allclose(received_ds, approved_ds, **self._float_tolerance.to_kwargs())
            except AssertionError as assertion_diff:
                stats_per_data_var = [(name, calculate_pixel_diff_stats(received_ds[name], approved_ds[name]))
                                      for name in common_data_vars]
                stats_per_data_var = [(n, s) for n, s in stats_per_data_var if not s.is_empty]
                diff_stats = '\n'.join([f"{n}: {str(s)}" for n, s in stats_per_data_var])
                if diff_stats:
                    diffs.append(Difference(diff_stats, DiffType.PIXEL_STATS))
                diffs.append(Difference(str(assertion_diff), DiffType.DATASET))

        return diffs
