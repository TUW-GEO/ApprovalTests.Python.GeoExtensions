import shutil
from datetime import datetime
from pathlib import Path

import pytest
from pytest import ExitCode

from factories import make_raster_at, make_zarr_at


@pytest.fixture
def standard_approval_test_directory():
    return Path(__file__).parent


@pytest.fixture
def make_tmp_approval_tif(standard_approval_test_directory):
    creates_files = []
    try:
        def _fn(values, name):
            file = make_raster_at(values, standard_approval_test_directory / name)
            creates_files.append(file)

        yield _fn
    finally:
        for f in creates_files:
            f.unlink()


@pytest.fixture
def make_tmp_approval_zarr(standard_approval_test_directory):
    creates_archives = []
    try:
        def _fn(values, name, ds_attrs=None, array_attrs=None):
            file = make_zarr_at(values, standard_approval_test_directory / name, ds_attrs, array_attrs)
            creates_archives.append(file)

        yield _fn
    finally:
        for a in creates_archives:
            shutil.rmtree(a)


def test_approvaltests_geo_data_settings(testdir, tmp_path):
    approval_root = tmp_path / "path/to/my/approved/geo/data/root/"
    approval_root.mkdir(parents=True, exist_ok=True)
    approval_input = approval_root / "subdir/to/input/data/"
    approval_input.mkdir(parents=True, exist_ok=True)
    approval_approved = approval_root / "subdir/to/approved/data/"
    approval_approved.mkdir(parents=True, exist_ok=True)
    testdir.makeini(f"""
        [pytest]
        approvaltests_geo_data_root = {approval_root}
        approvaltests_geo_input = subdir/to/input/data/
        approvaltests_geo_approved = subdir/to/approved/data/
    """)

    testdir.makepyfile(f"""
        import pytest
        def test_approved_geo_paths(approval_test_geo_data_root, approval_geo_input_directory, approved_geo_directory):
            assert approval_test_geo_data_root.as_posix() == '{approval_root.as_posix()}'
            assert approval_geo_input_directory.as_posix() == '{approval_input.as_posix()}'
            assert approved_geo_directory.as_posix() == '{approval_approved.as_posix()}'
    """)

    result = testdir.runpytest('-v')

    result.stdout.fnmatch_lines([
        '*::test_approved_geo_paths PASSED*',
    ])

    assert result.ret == 0


def test_approval_test_geo_data_root_option(testdir, tmp_path):
    custom_approval_root = tmp_path / "custom/path/to/my/approved/geo/data/root/"
    custom_approval_root.mkdir(parents=True, exist_ok=True)

    testdir.makeini("""
        [pytest]
        approvaltests_geo_data_root = /default/path/to/geo/test/data/root/
        approvaltests_geo_input = subdir/to/input/data/
        approvaltests_geo_approved = subdir/to/approved/data/
    """)

    testdir.makepyfile(f"""
        def test_custom_approval_test_geo_data_root(approval_test_geo_data_root):
            assert approval_test_geo_data_root.as_posix() == "{custom_approval_root.as_posix()}"
    """)

    result = testdir.runpytest(
        f'--approval-test-geo-data-root={custom_approval_root.as_posix()}',
        '-v'
    )

    result.stdout.fnmatch_lines([
        '*::test_custom_approval_test_geo_data_root PASSED*',
    ])

    assert result.ret == 0


def test_skip_tests_which_request_approval_root_but_it_does_not_exist(testdir, tmp_path):
    testdir.makeini("""
        [pytest]
        approvaltests_geo_data_root = /nonexistent/path/to/geo/test/data/root/
        approvaltests_geo_input = subdir/to/input/data/
        approvaltests_geo_approved = subdir/to/approved/data/
    """)

    testdir.makepyfile(f"""
        def test_skipped_because_of_missing_approval_root(approval_geo_input_directory):
            assert False
    """)

    result = testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        '*::test_skipped_because_of_missing_approval_root SKIPPED*',
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
            from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse
            from approvaltests.scrubbers import scrub_all_dates
            def test_verify_geo_tif(verify_geo_tif):
                verify_geo_tif("{tif_file.as_posix()}", 
                    options=GeoOptions().with_tags_scrubber(make_scrubber_recurse(scrub_all_dates)))
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


def test_verify_raster_as_geo_tif(testdir, make_tmp_approval_tif):
    make_tmp_approval_tif([[1.1]], "test_approvaltests_geo_extensions.test_verify_raster_as_geo_tif.approved.tif")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.factories import make_raster
            def test_verify_raster_as_geo_tif(verify_raster_as_geo_tif):
                verify_raster_as_geo_tif(make_raster([[1.0]]), options=GeoOptions()\\
                    .with_tolerance(rel_tol=0.05, abs_tol=0.051))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK


def test_verify_multiple_rasters_as_geo_tif(testdir, make_tmp_approval_tif):
    make_tmp_approval_tif([[1]],
                          "test_approvaltests_geo_extensions.test_verify_multiple_rasters_as_geo_tif.0.approved.tif")
    make_tmp_approval_tif([[2]],
                          "test_approvaltests_geo_extensions.test_verify_multiple_rasters_as_geo_tif.1.approved.tif")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.factories import make_raster
            from approvaltests.namer.default_namer_factory import NamerFactory
            from approval_utilities.utilities.exceptions.exception_collector import gather_all_exceptions_and_throw
            def test_verify_multiple_rasters_as_geo_tif(verify_raster_as_geo_tif):
                rasters = [make_raster([[1]]), make_raster([[2]])]
                gather_all_exceptions_and_throw([0, 1], lambda i: verify_raster_as_geo_tif(
                    rasters[i],
                    options=GeoOptions.from_options(NamerFactory.with_parameters(i))
                ))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')

    assert result.ret == ExitCode.OK


def test_verify_geo_zarr(testdir, make_tmp_approval_zarr, tmp_path):
    zarr_file = make_zarr_at([[1.0]], tmp_path / "a_zarr_to_test.zarr",
                             dict(some=datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S")))
    make_tmp_approval_zarr([[1.1]], "test_approvaltests_geo_extensions.test_verify_geo_zarr.approved.zarr")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse
            from approvaltests.scrubbers import scrub_all_dates
            def test_verify_geo_zarr(verify_geo_zarr):
                verify_geo_zarr("{zarr_file.as_posix()}", options=GeoOptions()\\
                    .with_tags_scrubber(make_scrubber_recurse(scrub_all_dates))
                    .with_tolerance(rel_tol=0.05, abs_tol=0.051))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK
