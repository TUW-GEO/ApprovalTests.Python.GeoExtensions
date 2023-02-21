import shutil
from pathlib import Path

from approvaltests.core import Comparator

from pytest_approvaltests_geo.differs.differ_of_geo_ncs import DifferOfGeoNcs


class CompareGeoNcs(Comparator, DifferOfGeoNcs):

    def compare(self, received_path: str, approved_path: str) -> bool:
        received_path = Path(received_path)
        approved_path = Path(approved_path)
        if not received_path.exists() or not approved_path.exists():
            return False

        diffs = self.diffs(received_path, approved_path)
        return len(diffs) == 0
