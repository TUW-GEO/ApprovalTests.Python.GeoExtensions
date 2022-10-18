from datetime import datetime
from pathlib import Path

import pytest
from pytest import ExitCode

from factories import make_raster_at


@pytest.fixture
def standard_approval_test_directory():
    return Path(__file__).parent


@pytest.fixture
def make_tmp_approval_raster(standard_approval_test_directory):
    creates_files = []
    try:
        def _fn(values, name):
            file = make_raster_at(values, standard_approval_test_directory / name)
            creates_files.append(file)

        yield _fn
    finally:
        for f in creates_files:
            f.unlink()


def test_approvaltests_geo_data_settings(testdir):
    testdir.makeini("""
        [pytest]
        approvaltests_geo_data_root = /path/to/my/approved/geo/data/root/
        approvaltests_geo_input = subdir/to/input/data/
        approvaltests_geo_approved = subdir/to/approved/data/
    """)

    testdir.makepyfile("""
        import pytest
        def test_approved_geo_paths(approval_test_geo_data_root, approval_geo_input_directory, approved_geo_directory):
            assert approval_test_geo_data_root.as_posix() == '/path/to/my/approved/geo/data/root'
            assert approval_geo_input_directory.as_posix() == '/path/to/my/approved/geo/data/root/subdir/to/input/data'
            assert approved_geo_directory.as_posix() == '/path/to/my/approved/geo/data/root/subdir/to/approved/data'
    """)

    result = testdir.runpytest('-v')

    result.stdout.fnmatch_lines([
        '*::test_approved_geo_paths PASSED*',
    ])

    assert result.ret == 0


def test_approval_test_geo_data_root_option(testdir):
    testdir.makeini("""
        [pytest]
        approvaltests_geo_data_root = /default/path/to/geo/test/data/root/
        approvaltests_geo_input = subdir/to/input/data/
        approvaltests_geo_approved = subdir/to/approved/data/
    """)

    testdir.makepyfile("""
        def test_custom_approval_test_geo_data_root(approval_test_geo_data_root):
            assert approval_test_geo_data_root.as_posix() == "/custom/geo/data/root"
    """)

    result = testdir.runpytest(
        '--approval-test-geo-data-root=/custom/geo/data/root',
        '-v'
    )

    result.stdout.fnmatch_lines([
        '*::test_custom_approval_test_geo_data_root PASSED*',
    ])

    assert result.ret == 0


def test_verify_geo_tif(testdir, tmp_path):
    root = tmp_path / "root"
    input_data = root / "input"
    approved = root / "approved"
    input_data.mkdir(parents=True, exist_ok=True)
    approved.mkdir(parents=True, exist_ok=True)

    testdir.makeini(f"""
        [pytest]
        approvaltests_geo_data_root = {root.as_posix()}
        approvaltests_geo_input = input
        approvaltests_geo_approved = approved
    """)

    tif_file = make_raster_at([[42]], tmp_path / "a_tif_to_test.tif",
                              dict(some=datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S")))

    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from approvaltests.scrubbers import scrub_all_dates
            from approval_utilities.utils import to_json
            def test_verify_geo_tif(verify_geo_tif):
                verify_geo_tif("{tif_file.as_posix()}", 
                    options=GeoOptions().with_tags_scrubber(lambda t: scrub_all_dates(to_json(t))))
        """)

    result = testdir.runpytest('-v')

    result.stdout.fnmatch_lines([
        '+    "some": "<date0>"',
    ])

    assert result.ret == ExitCode.TESTS_FAILED


def test_verify_multiple_geo_tiffs(testdir, tmp_path):
    root = tmp_path / "root"
    input_data = root / "input"
    approved = root / "approved"
    input_data.mkdir(parents=True, exist_ok=True)
    approved.mkdir(parents=True, exist_ok=True)

    testdir.makeini(f"""
        [pytest]
        approvaltests_geo_data_root = {root.as_posix()}
        approvaltests_geo_input = input
        approvaltests_geo_approved = approved
    """)

    tif_a = make_raster_at([[42]], tmp_path / "a_tif_to_test.tif", dict(band='VV'))
    tif_b = make_raster_at([[42]], tmp_path / "another_tif_to_test.tif", dict(band='VH'))

    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from approval_utilities.utilities.exceptions.exception_collector import gather_all_exceptions_and_throw
            def test_verify_multiple_geo_tiffs(verify_geo_tif):
                gather_all_exceptions_and_throw(["{tif_a.as_posix()}", "{tif_b.as_posix()}"], 
                    lambda tif: verify_geo_tif(tif, options=GeoOptions().with_scenario_by_tags(lambda t: (t['band'],))))
        """)

    result = testdir.runpytest('-v')

    result.stdout.fnmatch_lines([
        "*test_verify_multiple_geo_tiffs.VV.received.tif*",
        "*test_verify_multiple_geo_tiffs.VH.received.tif*",
    ])

    assert result.ret == ExitCode.TESTS_FAILED


def test_verify_raster_as_geo_tif(testdir, make_tmp_approval_raster):
    make_tmp_approval_raster([[42]], "test_approvaltests_geo_extensions.test_verify_raster_as_geo_tif.approved.tif")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.factories import make_raster
            from approval_utilities.utilities.exceptions.exception_collector import gather_all_exceptions_and_throw
            def test_verify_raster_as_geo_tif(verify_raster_as_geo_tif):
                verify_raster_as_geo_tif(make_raster([[42]]))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK
