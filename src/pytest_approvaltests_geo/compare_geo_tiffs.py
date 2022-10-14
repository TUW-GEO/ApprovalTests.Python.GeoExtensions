from pathlib import Path
from typing import Optional

from approvaltests.core import Comparator

from pytest_approvaltests_geo.geo_io import read_array_and_tags
from pytest_approvaltests_geo.scrubbers import TagsScrubber


class CompareGeoTiffs(Comparator):
    def __init__(self, tags_scrubber: Optional[TagsScrubber] = None):
        self._tags_scrubber = tags_scrubber

    def compare(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)
        if not received_path.exists() or not approved_path.exists():
            return False

        received_pixels, received_tags = read_array_and_tags(received_path)
        approved_pixels, approved_tags = read_array_and_tags(approved_path)

        if received_pixels.shape != approved_pixels.shape:
            return False

        if self._tags_scrubber:
            received_tags = self._tags_scrubber(received_tags)
            approved_tags = self._tags_scrubber(approved_tags)

        if received_tags != approved_tags:
            return False

        return received_pixels.equals(approved_pixels)
