from pathlib import Path
from typing import Optional, Union

import pytest
import rasterio
from approvaltests import verify_with_namer_and_writer, ExistingFileWriter, ScenarioNamer
from approvaltests.namer import NamerBase
from xarray import DataArray

from pytest_approvaltests_geo._version import __version__
from pytest_approvaltests_geo.comparators.compare_geo_tiffs import CompareGeoTiffs
from pytest_approvaltests_geo.comparators.compare_geo_zarrs import CompareGeoZarrs
from pytest_approvaltests_geo.existing_dir_writer import ExistingDirWriter
from pytest_approvaltests_geo.geo_options import GeoOptions
from pytest_approvaltests_geo.namer.stack_frame_namer_with_external_data_dir import StackFrameNamerWithExternalDataDir
from pytest_approvaltests_geo.reporters.report_geo_tiffs import ReportGeoTiffs
from pytest_approvaltests_geo.reporters.report_geo_zarrs import ReportGeoZarrs
from pytest_approvaltests_geo.scrubbers import RecursiveScrubber

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


def get_approval_root(config):
    custom_root = config.option.approval_test_geo_data_root
    if custom_root is not None:
        return Path(custom_root)

    root = config.getini('approvaltests_geo_data_root')
    if root:
        return Path(root)
    return None


def pytest_collection_modifyitems(config, items):
    approval_root = get_approval_root(config)
    if approval_root:
        skip_reason = f"needs {approval_root} to run."
    else:
        skip_reason = "needs an approval directory configured to run."
    skip_missing_dataset = pytest.mark.skip(reason=skip_reason)
    for item in items:
        if "approval_test_geo_data_root" in getattr(item, 'fixturenames', {}) and \
                (approval_root is None or not approval_root.exists()):
            item.add_marker(skip_missing_dataset)


@pytest.fixture(scope='module')
def approval_test_geo_data_root(request):
    custom_root = request.config.option.approval_test_geo_data_root
    if custom_root is not None:
        return Path(custom_root)

    root = request.config.getini('approvaltests_geo_data_root')
    if root:
        return Path(root)
    return None


@pytest.fixture(scope='module')
def approval_geo_input_directory(approval_test_geo_data_root, request):
    if approval_test_geo_data_root is not None:
        return approval_test_geo_data_root / request.config.getini('approvaltests_geo_input')
    return None


@pytest.fixture(scope='module')
def approved_geo_directory(approval_test_geo_data_root, request):
    if approval_test_geo_data_root is not None:
        return approval_test_geo_data_root / request.config.getini('approvaltests_geo_approved')
    return None


@pytest.fixture(scope='module')
def geo_data_namer_factory(approved_geo_directory):
    if approved_geo_directory is not None:
        return lambda: StackFrameNamerWithExternalDataDir(approved_geo_directory.as_posix())
    else:
        from approvaltests.namer.default_name import get_default_namer
        return get_default_namer


@pytest.fixture(scope='module')
def name_geo_scenario(geo_data_namer_factory):
    def scenario_namer(*scenario_names):
        return ScenarioNamer(geo_data_namer_factory(), *scenario_names)

    return scenario_namer


@pytest.fixture(scope='module')
def verify_geo_tif(verify_geo_tif_with_namer, geo_data_namer_factory):
    def _verify_fn(tile_file: PathConvertible,
                   *,  # enforce keyword arguments - https://www.python.org/dev/peps/pep-3102/
                   options: Optional[GeoOptions] = None):
        geo_data_namer = options.namer if options else None
        geo_data_namer = geo_data_namer or geo_data_namer_factory()
        geo_data_namer.set_extension(Path(tile_file).suffix)
        verify_geo_tif_with_namer(tile_file, geo_data_namer, options=options)

    return _verify_fn


@pytest.fixture(scope='module')
def verify_geo_tif_with_namer():
    def _verify_fn(tile_file: PathConvertible,
                   namer: NamerBase,
                   *,  # enforce keyword arguments - https://www.python.org/dev/peps/pep-3102/
                   options: Optional[GeoOptions] = None):
        options = options or GeoOptions()
        tif_comparator = CompareGeoTiffs(options.scrub_tags, options.tolerance)
        tif_reporter = ReportGeoTiffs(options.scrub_tags, options.tolerance)
        if options.has_scenario_by_tags():
            with rasterio.open(tile_file) as rds:
                namer = options.wrap_namer_in_tags_scenario(namer, rds.tags())
        options = options.with_comparator(tif_comparator)
        options = options.with_reporter(tif_reporter)
        verify_with_namer_and_writer(
            namer=namer,
            writer=ExistingFileWriter(tile_file, options),
            options=options)

    return _verify_fn


@pytest.fixture(scope='module')
def verify_raster_as_geo_tif(verify_geo_tif, tmp_path_factory):
    def _verify_fn(tile: DataArray,
                   *,  # enforce keyword arguments - https://www.python.org/dev/peps/pep-3102/
                   options: Optional[GeoOptions] = None):
        tile_file = tmp_path_factory.mktemp("raster_as_geo_tif") / "raster.tif"
        options = options or GeoOptions()
        options.tif_writer(tile_file, tile)
        verify_geo_tif(tile_file, options=options)

    return _verify_fn


@pytest.fixture(scope='module')
def verify_geo_zarr(geo_data_namer_factory):
    def _verify_fn(zarr_archive: PathConvertible,
                   *,  # enforce keyword arguments - https://www.python.org/dev/peps/pep-3102/
                   options: Optional[GeoOptions] = None):
        geo_data_namer = options.namer or geo_data_namer_factory()
        geo_data_namer.set_extension(Path(zarr_archive).suffix)
        options = options or GeoOptions()
        zarr_comparator = CompareGeoZarrs(options.scrub_tags, options.tolerance)
        zarr_reporter = ReportGeoZarrs(options.scrub_tags, options.tolerance)
        options = options.with_comparator(zarr_comparator)
        options = options.with_reporter(zarr_reporter)
        verify_with_namer_and_writer(
            namer=geo_data_namer,
            writer=ExistingDirWriter(zarr_archive),
            options=options)

    return _verify_fn
