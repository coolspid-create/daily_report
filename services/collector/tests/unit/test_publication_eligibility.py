from report_collector.services.publication_eligibility import is_public_report_source


def test_press_release_sources_are_excluded_from_public_snapshots() -> None:
    assert not is_public_report_source("mof-press")
    assert not is_public_report_source("fsc-policy")


def test_report_sources_remain_eligible_for_public_snapshots() -> None:
    assert is_public_report_source("kotra-market-news")
    assert is_public_report_source("hana-research")
