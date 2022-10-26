import os
from dataclasses import dataclass
from difflib import unified_diff
from enum import Enum
from pathlib import Path
from typing import Sequence, Optional

import numpy as np
from approval_utilities.utils import to_json

from pytest_approvaltests_geo.geo_io import read_array_and_tags
from pytest_approvaltests_geo.scrubbers import TagsScrubber


class DiffType(Enum):
    TAGS = 0
    PIXEL_STATS = 0


@dataclass
class Difference:
    description: str
    type: DiffType


class DifferOfGeoTiffs:
    def __init__(self, tags_scrubber: Optional[TagsScrubber] = None):
        self._tags_scrubber = tags_scrubber

    def diffs(self, received_path: Path, approved_path: Path) -> Sequence[Difference]:
        diffs = []
        with read_array_and_tags(received_path) as (received_pixels, received_tags), \
                read_array_and_tags(approved_path) as (approved_pixels, approved_tags):
            diff_tags = self._calculate_tags_diff(approved_path, approved_tags, received_path, received_tags)
            if diff_tags:
                diffs.append(Difference(diff_tags, DiffType.TAGS))
            diff_pixels = self._calculate_pixel_diff(approved_pixels, received_pixels)
            if diff_pixels:
                diffs.append(Difference(diff_pixels, DiffType.PIXEL_STATS))
        return diffs

    def _calculate_tags_diff(self, approved_path, approved_tags, received_path, received_tags):
        if self._tags_scrubber:
            approved_text = f"{self._tags_scrubber(approved_tags)}"
            received_text = f"{self._tags_scrubber(received_tags)}"
        else:
            approved_text = f"{to_json(approved_tags)}\n"
            received_text = f"{to_json(received_tags)}\n"
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
