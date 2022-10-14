from approvaltests import StackFrameNamer


class StackFrameNamerWithExternalDataDir(StackFrameNamer):
    def __init__(self, data_root):
        super().__init__()
        self._data_root = data_root

    def get_directory(self) -> str:
        return self._data_root
