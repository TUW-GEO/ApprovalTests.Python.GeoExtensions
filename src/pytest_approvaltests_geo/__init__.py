from pathlib import Path

from pytest_approvaltests_geo._version import __version__
import pytest

APPROVAL_TEST_GEO_DATA_ROOT_OPTION = "--approval-test-geo-data-root"


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
