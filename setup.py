import re
from pathlib import Path

from setuptools import setup

version_file = Path(__file__).parent / "src/pytest_approvaltests_geo/_version.py"
version_line = re.search(r'__version__ = ["\']\d\.\d\.\d(\.dev\d)?["\']', version_file.read_text()).group(0)
version_str = re.search(r'\d\.\d\.\d(\.dev\d)?', version_line).group(0)
setup(version=version_str)