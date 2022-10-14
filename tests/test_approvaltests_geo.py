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
