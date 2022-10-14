from datetime import datetime

from pytest import ExitCode

from factories import make_raster_at


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
            from pytest_approvaltests_geo import GeoOptions
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
