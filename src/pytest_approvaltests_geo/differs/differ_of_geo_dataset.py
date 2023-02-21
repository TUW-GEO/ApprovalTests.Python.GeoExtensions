from pathlib import Path
from typing import Sequence, Callable

import xarray as xr
from xarray import Dataset

from pytest_approvaltests_geo.differs.difference import Difference, add_common_meta_data_diffs, \
    calculate_pixel_diff_stats, DiffType
from pytest_approvaltests_geo.scrubbers import scrub_xarray_data

DatasetOpener = Callable[[Path], Dataset]


class DifferOfGeoDataset:
    def __init__(self, opener: DatasetOpener, recursive_scrubber, float_tolerance):
        self._opener = opener
        self._recursive_scrubber = recursive_scrubber
        self._float_tolerance = float_tolerance

    def diffs(self, received_path: Path, approved_path: Path) -> Sequence[Difference]:
        diffs = []
        with self._opener(received_path) as received_ds, self._opener(approved_path) as approved_ds:
            received_ds = scrub_xarray_data(received_ds, self._recursive_scrubber)
            approved_ds = scrub_xarray_data(approved_ds, self._recursive_scrubber)
            diffs = add_common_meta_data_diffs(received_ds, approved_ds, diffs)

            try:
                xr.testing.assert_allclose(received_ds, approved_ds, **self._float_tolerance.to_kwargs())
            except AssertionError as assertion_diff:
                common_data_vars = set(received_ds.data_vars) & set(approved_ds.data_vars)
                stats_per_data_var = [(name, calculate_pixel_diff_stats(received_ds[name], approved_ds[name]))
                                      for name in common_data_vars]
                stats_per_data_var = [(n, s) for n, s in stats_per_data_var if not s.is_empty]
                diff_stats = '\n'.join([f"{n}: {str(s)}" for n, s in stats_per_data_var])
                if diff_stats:
                    diffs.append(Difference(diff_stats, DiffType.PIXEL_STATS))
                diffs.append(Difference(str(assertion_diff), DiffType.DATASET))

        return diffs
