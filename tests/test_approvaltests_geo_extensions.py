from datetime import datetime
from pathlib import Path

import pytest
from approval_utilities.utilities.multiline_string_utils import remove_indentation_from
from pytest import ExitCode

from factories import make_raster_at, make_zarr_at, make_nc_at


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
    make_standard_geo_data_setting(testdir, tmp_path)

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


def make_standard_geo_data_setting(testdir, tmp_path):
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

    return root, input_data, approved


def test_verify_multiple_geo_tiffs(testdir, tmp_path):
    make_standard_geo_data_setting(testdir, tmp_path)

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


def test_verify_data_frame_using_geo_tif_verification(testdir, tmp_path):
    make_standard_geo_data_setting(testdir, tmp_path)

    tif_a = make_raster_at([[42]], tmp_path / "a.tif")
    tif_b = make_raster_at([[42]], tmp_path / "b.tif")

    testdir.makepyfile(f"""
            from pandas import DataFrame
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from approval_utilities.utilities.exceptions.exception_collector import gather_all_exceptions_and_throw
            def test_verify_geo_tif_data_frame(verify_data_frame_using, verify_geo_tif):
                df = DataFrame(dict(filepath=["{tif_a.as_posix()}", "{tif_b.as_posix()}"], 
                               param_a=[0, 0], 
                               param_b=['A', 'B']))
                verify_data_frame_using(verify_geo_tif, 'param_a', 'param_b')(df)
        """)

    result = testdir.runpytest('-v')

    result.stdout.fnmatch_lines([
        "*test_verify_data_frame_using_geo_tif_verification.0.A.received.tif*",
        "*test_verify_data_frame_using_geo_tif_verification.0.B.received.tif*",
    ])


def test_verify_data_frame_passes_along_geo_options(testdir, tmp_path):
    make_standard_geo_data_setting(testdir, tmp_path)

    tif_file = make_raster_at([[42]], tmp_path / "a_tif_to_test.tif",
                              dict(some=datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S")))

    testdir.makepyfile(f"""
            from pandas import DataFrame
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse
            from approvaltests.scrubbers import scrub_all_dates
            def test_verify_geo_tif(verify_data_frame_using, verify_geo_tif):
                df = DataFrame(dict(filepath=["{tif_file.as_posix()}"],  param_a=[0]))
                verify_data_frame_using(verify_geo_tif, 'param_a')(df, 
                    options=GeoOptions().with_tags_scrubber(make_scrubber_recurse(scrub_all_dates)))
        """)

    result = testdir.runpytest('-v')

    result.stdout.fnmatch_lines([
        '+    "some": "<date0>"',
    ])


def test_verify_raster_as_geo_tif(testdir, tmp_path):
    _, _, approved_dir = make_standard_geo_data_setting(testdir, tmp_path)

    make_raster_at([[1.0]],
                   approved_dir / "test_approvaltests_geo_extensions.test_verify_raster_as_geo_tif.approved.tif")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.factories import make_raster
            def test_verify_raster_as_geo_tif(verify_raster_as_geo_tif):
                verify_raster_as_geo_tif(make_raster([[1.0]]))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK


def test_verify_raster_as_geo_tif_with_tolerance(testdir, tmp_path):
    _, _, approved_dir = make_standard_geo_data_setting(testdir, tmp_path)

    make_raster_at([[1.1]],
                   approved_dir / "test_approvaltests_geo_extensions.test_verify_raster_as_geo_tif_with_tolerance.approved.tif")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.factories import make_raster
            def test_verify_raster_as_geo_tif(verify_raster_as_geo_tif):
                verify_raster_as_geo_tif(make_raster([[1.0]]), options=GeoOptions()\\
                    .with_tolerance(rel_tol=0.05, abs_tol=0.051))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK


def test_verify_raster_as_geo_tif_with_custom_tif_writer(testdir, tmp_path):
    _, _, approved_dir = make_standard_geo_data_setting(testdir, tmp_path)
    make_raster_at([[2.0]],
                   approved_dir / "test_approvaltests_geo_extensions.test_verify_raster_as_geo_tif_with_custom_tif_writer.approved.tif")

    testdir.makepyfile(f"""
            import rioxarray
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.factories import make_raster
            def test_verify_raster_as_geo_tif(verify_raster_as_geo_tif):
                verify_raster_as_geo_tif(make_raster([[1.0]]), options=GeoOptions()\\
                    .with_tif_writer(lambda f, a: make_raster([[2.0]]).rio.to_raster(f)))
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


def test_verify_geo_zarr(testdir, tmp_path):
    _, _, approved_dir = make_standard_geo_data_setting(testdir, tmp_path)

    old_date = datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S")
    zarr_file = make_zarr_at([[1.0]], tmp_path / "a_zarr_to_test.zarr",
                             dict(some=old_date), extra_coords={'meta': ('band', [old_date])})
    new_date = datetime(2022, 1, 2).strftime("%Y-%m-%d %H:%M:%S")
    make_zarr_at([[1.1]], approved_dir / "test_approvaltests_geo_extensions.test_verify_geo_zarr.approved.zarr",
                 dict(some=new_date), extra_coords={'meta': ('band', [new_date])})
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse, make_scrubber_sequential
            from approvaltests.scrubbers import scrub_all_dates
            def test_verify_geo_zarr(verify_geo_zarr):
                verify_geo_zarr("{zarr_file.as_posix()}", options=GeoOptions()\\
                    .with_tags_scrubber(make_scrubber_recurse(scrub_all_dates))
                    .with_coords_scrubber(make_scrubber_sequential(scrub_all_dates))
                    .with_tolerance(rel_tol=0.05, abs_tol=0.051))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK


def test_verify_parametrized_geo_zarr(testdir, tmp_path):
    _, _, approved_dir = make_standard_geo_data_setting(testdir, tmp_path)

    zarr_file = make_zarr_at([[1.0]], tmp_path / "a_zarr_to_test.zarr")
    make_zarr_at([[1.0]], approved_dir /
                 "test_approvaltests_geo_extensions.test_verify_parametrized_geo_zarr.scenario0.approved.zarr")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from approvaltests import Options
            def test_verify_geo_zarr(verify_geo_zarr, name_geo_scenario):
                verify_geo_zarr("{zarr_file.as_posix()}", options=GeoOptions\\
                    .from_options(Options().with_namer(name_geo_scenario("scenario0"))))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK


def test_verify_geo_zarr_without_options(testdir, tmp_path):
    _, _, approved_dir = make_standard_geo_data_setting(testdir, tmp_path)

    zarr_file = make_zarr_at([[1.0]], tmp_path / "a_zarr_to_test.zarr")
    make_zarr_at([[1.0]], approved_dir /
                 "test_approvaltests_geo_extensions.test_verify_geo_zarr_without_options.approved.zarr")
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from approvaltests import Options
            def test_verify_geo_zarr(verify_geo_zarr, name_geo_scenario):
                verify_geo_zarr("{zarr_file.as_posix()}")
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK


def test_verify_geo_nc(testdir, tmp_path):
    _, _, approved_dir = make_standard_geo_data_setting(testdir, tmp_path)

    nc_file = make_nc_at([[1.0]], tmp_path / "a_nc_to_test.nc",
                         dict(some=datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M:%S")))
    make_nc_at([[1.1]], approved_dir / "test_approvaltests_geo_extensions.test_verify_geo_nc.approved.nc",
               dict(some=datetime(2022, 1, 2).strftime("%Y-%m-%d %H:%M:%S")))
    testdir.makepyfile(f"""
            from pytest_approvaltests_geo.geo_options import GeoOptions
            from pytest_approvaltests_geo.scrubbers import make_scrubber_recurse
            from approvaltests.scrubbers import scrub_all_dates
            def test_verify_geo_nc(verify_geo_nc):
                verify_geo_nc("{nc_file.as_posix()}", options=GeoOptions()\\
                    .with_tags_scrubber(make_scrubber_recurse(scrub_all_dates))
                    .with_tolerance(rel_tol=0.05, abs_tol=0.051))
        """)

    result = testdir.runpytest(Path(testdir.tmpdir), '-v')
    assert result.ret == ExitCode.OK


def test_doc_tests_still_working(pytester, tmp_path):
    make_standard_geo_data_setting(pytester, tmp_path)

    module = pytester.mkpydir("some_module")
    (module / "a_class_with_doc.py").write_text(remove_indentation_from(f'''
            class AClassWithDoc:
                """
                >>> AClassWithDoc(42).the_answer
                42
                """
                def __init__(self, answer):
                    self.the_answer = answer
            '''))

    result = pytester.runpytest(Path(pytester.path), '--doctest-modules')
    assert result.ret == ExitCode.OK
