import os
from difflib import unified_diff
from pathlib import Path
from typing import Sequence, Optional

import xarray as xr
from approval_utilities.utils import to_json

from pytest_approvaltests_geo.differs.difference import DiffType, Difference, calculate_pixel_diff_stats, \
    add_common_meta_data_diffs
from pytest_approvaltests_geo.float_utils import Tolerance
from pytest_approvaltests_geo.geo_io import read_array_and_tags
from pytest_approvaltests_geo.scrubbers import RecursiveScrubber, identity_recursive_scrubber, scrub_xarray_metadata


class DifferOfGeoTiffs:
    def __init__(self, recursive_scrubber: Optional[RecursiveScrubber] = None,
                 float_tolerance: Optional[Tolerance] = None):
        self._recursive_scrubber = recursive_scrubber or identity_recursive_scrubber
        self._float_tolerance = float_tolerance or Tolerance()

    def diffs(self, received_path: Path, approved_path: Path) -> Sequence[Difference]:
        diffs = []
        with read_array_and_tags(received_path) as (received_pixels, received_tags), \
                read_array_and_tags(approved_path) as (approved_pixels, approved_tags):
            diff_tags = self._calculate_tags_diff(approved_path, approved_tags, received_path, received_tags)
            if diff_tags:
                diffs.append(Difference(diff_tags, DiffType.TAGS))

            received_pixels = scrub_xarray_metadata(received_pixels, self._recursive_scrubber)
            approved_pixels = scrub_xarray_metadata(approved_pixels, self._recursive_scrubber)
            diffs = add_common_meta_data_diffs(received_pixels, approved_pixels, diffs)

            try:
                xr.testing.assert_allclose(received_pixels, approved_pixels, **self._float_tolerance.to_kwargs())
            except AssertionError as assertion_diff:
                diff_px_stats = calculate_pixel_diff_stats(approved_pixels, received_pixels)
                diffs.append(Difference(f"pixel differences statistics:\n{str(diff_px_stats)}", DiffType.PIXEL_STATS))
                diffs.append(Difference(str(assertion_diff), DiffType.DATASET))
        return diffs

    def _calculate_tags_diff(self, approved_path, approved_tags, received_path, received_tags):
        approved_text = f"{to_json(self._recursive_scrubber(approved_tags))}\n"
        received_text = f"{to_json(self._recursive_scrubber(received_tags))}\n"
        return "\n".join(unified_diff(
            approved_text.splitlines(),
            received_text.splitlines(),
            os.path.basename(approved_path),
            os.path.basename(received_path)
        )).strip()
