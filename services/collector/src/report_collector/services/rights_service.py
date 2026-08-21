from report_collector.domain.enums import DeliveryMode, RightsStatus

SESSION_QUERY_MARKERS = ("token=", "signature=", "expires=", "x-amz-")


def is_session_dependent_url(url: str) -> bool:
    lowered = url.lower()
    return any(marker in lowered for marker in SESSION_QUERY_MARKERS)


def choose_delivery(
    rights: RightsStatus,
    official_file_stable: bool,
    session_dependent: bool,
    mirrored_file_exists: bool,
    source_available: bool,
) -> DeliveryMode:
    if rights is RightsStatus.BLOCKED:
        return DeliveryMode.BLOCKED
    if official_file_stable and not session_dependent:
        return DeliveryMode.DIRECT_OFFICIAL_FILE
    if session_dependent or source_available:
        return DeliveryMode.OFFICIAL_PAGE_ONLY
    if rights is RightsStatus.FILE_UPLOAD_ALLOWED and mirrored_file_exists:
        return DeliveryMode.MIRRORED_ALLOWED
    return DeliveryMode.SUMMARY_ONLY
