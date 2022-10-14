import os
from difflib import unified_diff, context_diff
from pathlib import Path

import numpy as np
from approval_utilities.utils import to_json
from approvaltests import Reporter
from approvaltests.reporters import get_command_text
from approvaltests.scrubbers import scrub_all_dates, scrub_all_guids
from xarray import DataArray

from pytest_approvaltests_geo.geo_io import read_array_and_tags


class ReportGeoTiffs(Reporter):
    def report(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)

        if not approved_path.is_file():
            self._create_empty_geotiff(approved_path)

        received_pixels, received_tags = read_array_and_tags(received_path)
        approved_pixels, approved_tags = read_array_and_tags(approved_path)

        diff_tags = self._calculate_tags_diff(approved_path, approved_tags, received_path, received_tags)
        diff_pixels_msg = self._calculate_pixel_diff(approved_pixels, received_pixels)

        if diff_tags:
            diff_tags = f"Differences in meta data:\n{diff_tags}"
        if diff_pixels_msg:
            diff_pixels_msg = f"Differences in pixel data:\n{diff_pixels_msg}"
        if diff_tags or diff_pixels_msg:
            to_approve_msg = \
                f"To approve run:\n {get_command_text(received_path.as_posix(), approved_path.as_posix())}"
            print('\n'.join([diff_tags, diff_pixels_msg, to_approve_msg]))
        return True

    @staticmethod
    def _calculate_tags_diff(approved_path, approved_tags, received_path, received_tags):
        approved_text = scrub_all_dates(f"{to_json(approved_tags)}\n")
        received_text = scrub_all_dates(f"{to_json(received_tags)}\n")
        approved_text = scrub_all_guids(approved_text)
        received_text = scrub_all_guids(received_text)
        return "\n".join(unified_diff(
            approved_text.splitlines(),
            received_text.splitlines(),
            os.path.basename(approved_path),
            os.path.basename(received_path)
        )).strip()

    @staticmethod
    def _calculate_pixel_diff(approved_pixels, received_pixels):
        diff_pixels = np.abs(received_pixels - approved_pixels)
        diff_min = np.nanmin(diff_pixels)
        diff_max = np.nanmax(diff_pixels)
        diff_mean = np.nanmean(diff_pixels)
        diff_median = np.nanmedian(diff_pixels)
        if diff_min != 0 or diff_max != 0:
            return f"pixel differences statistics:\n" \
                   f"min={diff_min}, max={diff_max}, mean={diff_mean}, median={diff_median}"
        return ""

    @staticmethod
    def _create_empty_geotiff(path: Path):
        DataArray().rio.to_raster(path, compress='ZSTD')
