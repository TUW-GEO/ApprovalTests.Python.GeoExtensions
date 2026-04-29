from pytest_approvaltests_geo.scrubbers import scrub_all_short_commits, scrub_yeoda_datacube_metadata


def test_scrub_all_yeoda_metadata():
    assert scrub_yeoda_datacube_metadata("2018-09-12 12:00:00;20220101T235959;ae2df71;v1.0.2") == \
           "<date0>;<yeoda_date0>;<short_commit_0>;<tag_0>"


def test_g_prefixed_short_commit_is_scrubbed_like_bare_hash():
    assert scrub_all_short_commits("gae2df71") == "<short_commit_0>"
