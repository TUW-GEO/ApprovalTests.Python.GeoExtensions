from pytest_approvaltests_geo.scrubbers import scrub_yeoda_datacube_metadata


def test_scrub_all_yeoda_metadata():
    assert scrub_yeoda_datacube_metadata("2018-09-12 12:00:00;20220101T235959;ae2df71;v1.0.2") == \
           "<date0>;<yeoda_date0>;<short_commit_0>;<tag_0>"
