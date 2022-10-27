import shutil
from pathlib import Path

from approvaltests.core import Comparator

from pytest_approvaltests_geo.differs.differ_of_geo_zarrs import DifferOfGeoZarrs


class CompareGeoZarrs(Comparator, DifferOfGeoZarrs):

    def compare(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)
        if not received_path.exists() or not approved_path.exists():
            return False

        is_identical = len(self.diffs(received_path, approved_path)) == 0
        if is_identical:
            shutil.rmtree(received_path)
            received_path.touch()  # TODO: fix so approval tests has something to delete
        return is_identical
