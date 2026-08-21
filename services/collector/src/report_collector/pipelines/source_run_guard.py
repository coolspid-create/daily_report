import asyncio
from collections.abc import Awaitable

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
    except TimeoutError:
        repository.fail_run(
            source_id,
            "SOURCE_TIMEOUT",
            f"Source run exceeded its {timeout_seconds}-second limit.",
        )
    except Exception as error:
        repository.fail_run(source_id, "SOURCE_ERROR", _error_message(error))
    return CollectionResult(source_id, 0, 1, repository.get_cursor(source_id))


def _error_message(error: Exception) -> str:
    detail = str(error).strip()
    return detail or error.__class__.__name__
