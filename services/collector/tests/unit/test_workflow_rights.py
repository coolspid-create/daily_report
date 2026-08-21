import pytest
from report_collector.domain.enums import DeliveryMode, ProcessingState, RightsStatus
from report_collector.domain.errors import InvalidTransitionError
from report_collector.services.rights_service import choose_delivery
from report_collector.services.workflow_service import transition


def test_workflow_transition() -> None:
    assert (
        transition(ProcessingState.DISCOVERED, ProcessingState.DETAIL_FETCHED)
        is ProcessingState.DETAIL_FETCHED
    )
    with pytest.raises(InvalidTransitionError):
        transition(ProcessingState.DISCOVERED, ProcessingState.PUBLISHED)


@pytest.mark.parametrize(
    ("rights", "stable", "session", "mirrored", "source", "expected"),
    [
        (RightsStatus.BLOCKED, True, False, False, True, DeliveryMode.BLOCKED),
        (RightsStatus.LINK_ONLY, True, False, False, True, DeliveryMode.DIRECT_OFFICIAL_FILE),
        (RightsStatus.LINK_ONLY, False, True, False, True, DeliveryMode.OFFICIAL_PAGE_ONLY),
        (
            RightsStatus.FILE_UPLOAD_ALLOWED,
            False,
            False,
            True,
            False,
            DeliveryMode.MIRRORED_ALLOWED,
        ),
        (RightsStatus.LINK_ONLY, False, False, False, False, DeliveryMode.SUMMARY_ONLY),
    ],
)
def test_delivery_policy(rights, stable, session, mirrored, source, expected) -> None:
    assert choose_delivery(rights, stable, session, mirrored, source) is expected
