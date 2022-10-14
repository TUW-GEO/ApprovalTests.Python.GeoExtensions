from pathlib import Path
from typing import Optional, Union, Dict

import pytest
from approvaltests import Options, verify_with_namer_and_writer, ExistingFileWriter, StackFrameNamer, Namer

from pytest_approvaltests_geo._version import __version__
from pytest_approvaltests_geo.compare_geo_tiffs import CompareGeoTiffs
from pytest_approvaltests_geo.report_geo_tiffs import ReportGeoTiffs
from pytest_approvaltests_geo.scrubbers import TagsScrubber

APPROVAL_TEST_GEO_DATA_ROOT_OPTION = "--approval-test-geo-data-root"

PathConvertible = Union[Path, str]


def pytest_addoption(parser):
    group = parser.getgroup('pytest-approvaltests-geo')
    group.addoption(APPROVAL_TEST_GEO_DATA_ROOT_OPTION,
                    default=None,
                    help="specify local approval test data root")

    parser.addini('approvaltests_geo_data_root',
                  'Path to your approval test geo data root containing your input and approved files', type='string')
    parser.addini('approvaltests_geo_input',
                  'Subdirectory within the approval test geo data root containing your input files', type='string')
    parser.addini('approvaltests_geo_approved',
                  'Subdirectory within the approval test geo data root containing your approved files', type='string')


@pytest.fixture
def approval_test_geo_data_root(request):
    custom_root = request.config.option.approval_test_geo_data_root
    if custom_root is not None:
        return Path(custom_root)
    return Path(request.config.getini('approvaltests_geo_data_root'))


@pytest.fixture
def approval_geo_input_directory(approval_test_geo_data_root, request):
    return approval_test_geo_data_root / request.config.getini('approvaltests_geo_input')


@pytest.fixture
def approved_geo_directory(approval_test_geo_data_root, request):
    return approval_test_geo_data_root / request.config.getini('approvaltests_geo_approved')


class GeoOptions(Options):
    _TAGS_SCRUBBER_FUNC = "tags_scrubber_func"

    def scrub_tags(self, data: Dict):
        if self.has_tags_scrubber():
            return self.fields[GeoOptions._TAGS_SCRUBBER_FUNC](data)
        return data

    def with_tags_scrubber(self, scrubber_func: TagsScrubber) -> "GeoOptions":
        return GeoOptions({**self.fields, **{GeoOptions._TAGS_SCRUBBER_FUNC: scrubber_func}})

    def has_tags_scrubber(self):
        return GeoOptions._TAGS_SCRUBBER_FUNC in self.fields


class StackFrameNamerWithExternalDataDir(StackFrameNamer):
    def __init__(self, data_root):
        super().__init__()
        self._data_root = data_root

    def get_directory(self) -> str:
        return self._data_root


@pytest.fixture
def geo_data_namer(approved_geo_directory):
    return StackFrameNamerWithExternalDataDir(approved_geo_directory.as_posix())


@pytest.fixture
def verify_geo_tif(verify_geo_tif_with_namer, geo_data_namer):
    def _verify_fn(tile_file: PathConvertible,
                   *,  # enforce keyword arguments - https://www.python.org/dev/peps/pep-3102/
                   options: Optional[GeoOptions] = None):
        geo_data_namer.set_extension(Path(tile_file).suffix)
        verify_geo_tif_with_namer(tile_file, geo_data_namer, options=options)

    return _verify_fn


@pytest.fixture
def verify_geo_tif_with_namer():
    def _verify_fn(tile_file: PathConvertible,
                   namer: Namer,
                   *,  # enforce keyword arguments - https://www.python.org/dev/peps/pep-3102/
                   options: Optional[GeoOptions] = None):
        options = options or GeoOptions()
        tif_comparator = CompareGeoTiffs(options.scrub_tags)
        tif_reporter = ReportGeoTiffs(options.scrub_tags)
        options = options.with_comparator(tif_comparator)
        options = options.with_reporter(tif_reporter)
        verify_with_namer_and_writer(
            namer=namer,
            writer=ExistingFileWriter(tile_file, options),
            options=options)

    return _verify_fn
