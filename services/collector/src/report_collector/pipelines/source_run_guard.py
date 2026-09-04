import asyncio
from collections.abc import Awaitable

from report_collector.domain.errors import SourceMaintenanceError
from report_collector.pipelines.collect_source import CollectionResult
from report_collector.repositories.source_repository import SourceRepository


async def run_with_source_timeout(
    source_id: str,
    repository: SourceRepository,
    timeout_seconds: int,
    operation: Awaitable[CollectionResult],
) -> CollectionResult:
    try:
        return await asyncio.wait_for(operation, timeout=timeout_seconds)
    except SourceMaintenanceError as error:
        repository.record_maintenance_run(source_id, str(error))
    except TimeoutError:
        repository.fail_run(
            source_id,
            "SOURCE_TIMEOUT",
            f"Source run exceeded its {timeout_seconds}-second limit.",
        )
    except Exception as error:
        code, msg = classify_error(error)
        repository.fail_run(source_id, code, msg)
    return CollectionResult(source_id, 0, 1, repository.get_cursor(source_id))


def classify_error(error: Exception) -> tuple[str, str]:
    detail = str(error).strip()
    name = error.__class__.__name__
    message = detail or name
    if "SourceMaintenanceError" in name:
        return "SOURCE_MAINTENANCE", message
    if "SourceTimeout" in name or "TimeoutError" in name:
        return "SOURCE_TIMEOUT", message
    if "ConnectTimeout" in name or "ConnectTimeout" in message:
        return "CONNECT_TIMEOUT", message
    if "ConnectError" in name or "ConnectError" in message:
        return "CONNECT_ERROR", message
    if "ReadTimeout" in name or "ReadTimeout" in message:
        return "READ_TIMEOUT", message
    if "HTTPStatusError" in name or hasattr(error, "response"):
        response = getattr(error, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code:
            return f"HTTP_STATUS_{status_code}", message
        return "HTTP_ERROR", message
    if "TooManyRedirects" in name:
        return "TOO_MANY_REDIRECTS", message
    if "SourceParseError" in name:
        return "SOURCE_PARSE_ERROR", message
    return "SOURCE_ERROR", message
