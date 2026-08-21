from report_collector.domain.enums import ProcessingState
from report_collector.domain.errors import InvalidTransitionError

ALLOWED: dict[ProcessingState, set[ProcessingState]] = {
    ProcessingState.DISCOVERED: {ProcessingState.DETAIL_FETCHED},
    ProcessingState.DETAIL_FETCHED: {
        ProcessingState.FILE_IDENTIFIED,
        ProcessingState.RIGHTS_EVALUATED,
    },
    ProcessingState.FILE_IDENTIFIED: {
        ProcessingState.FILE_DOWNLOADED,
        ProcessingState.RIGHTS_EVALUATED,
    },
    ProcessingState.FILE_DOWNLOADED: {ProcessingState.FILE_VALIDATED, ProcessingState.FILE_INVALID},
    ProcessingState.FILE_VALIDATED: {ProcessingState.TEXT_EXTRACTED, ProcessingState.OCR_REQUIRED},
    ProcessingState.TEXT_EXTRACTED: {ProcessingState.DEDUPLICATED},
    ProcessingState.OCR_REQUIRED: {ProcessingState.DEDUPLICATED},
    ProcessingState.DEDUPLICATED: {ProcessingState.CLASSIFIED, ProcessingState.MERGED},
    ProcessingState.CLASSIFIED: {ProcessingState.SUMMARIZED, ProcessingState.SUMMARY_FAILED},
    ProcessingState.SUMMARIZED: {ProcessingState.RIGHTS_EVALUATED},
    ProcessingState.SUMMARY_FAILED: {ProcessingState.RIGHTS_EVALUATED},
    ProcessingState.RIGHTS_EVALUATED: {ProcessingState.NEEDS_REVIEW},
    ProcessingState.NEEDS_REVIEW: {ProcessingState.APPROVED, ProcessingState.REJECTED},
    ProcessingState.APPROVED: {ProcessingState.PUBLISHED},
}


def transition(current: ProcessingState, target: ProcessingState) -> ProcessingState:
    if target not in ALLOWED.get(current, set()):
        raise InvalidTransitionError(f"{current} -> {target} is not allowed")
    return target
