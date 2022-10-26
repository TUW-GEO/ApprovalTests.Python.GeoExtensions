import shutil
from pathlib import Path

from approvaltests import Writer


class ExistingDirWriter(Writer):
    def __init__(self, dir_name: str) -> None:
        self.dir_name = dir_name

    def write_received_file(self, received_file: str) -> str:
        if Path(received_file).exists():
            shutil.rmtree(received_file)
        shutil.copytree(self.dir_name, received_file)
        return received_file
