from pytest_approvaltests_geo._version import __version__
import pytest


def pytest_addoption(parser):
    group = parser.getgroup('pytest-approvaltests-geo')
    group.addoption(
        '--foo',
        action='store',
        dest='dest_foo',
        default='{% now "utc", "%Y" %}',
        help='Set the value for the fixture "bar".'
    )

    parser.addini('HELLO', 'Dummy pytest.ini setting')


@pytest.fixture
def bar(request):
    return request.config.option.dest_foo