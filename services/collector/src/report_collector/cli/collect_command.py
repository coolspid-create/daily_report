import asyncio
import json
import os
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from report_collector.adapters.factory import build_adapter
from report_collector.config.settings import Settings
from report_collector.config.source_config import load_source_config
from report_collector.domain.models import SourceDocument
from report_collector.pipelines.collect_source import CollectionResult, collect_source
from report_collector.pipelines.process_source_document import SourceDocumentProcessor
from report_collector.pipelines.source_run_guard import run_with_source_timeout
from report_collector.providers.browser.playwright_browser import PlaywrightBrowserRenderer
from report_collector.providers.http.http_client import PublicHttpClient
from report_collector.repositories.source_repository import MemorySourceRepository, SourceRepository
from report_collector.repositories.supabase.postgres_source_repository import (
    PostgresSourceRepository,
    load_active_source_slugs,
)


@dataclass(frozen=True)
class CollectBatchSummary:
    failed_sources: int
    new_documents_count: int
    discovered_count: int


async def run_source(
    config_path: Path,
    schema_path: Path,
    refresh_recent: bool = False,
    browser: PlaywrightBrowserRenderer | None = None,
) -> CollectionResult:
    config = load_source_config(config_path, schema_path)
    settings = Settings.from_environment()
    http = PublicHttpClient(config.timeout_seconds, config.max_retries, config.request_delay_ms)
    adapter = build_adapter(config, http, browser if config.adapter.value == "rendered_board" else None)
    repository, after_save = _build_processing_pipeline(settings, schema_path, http)
    kst_now = datetime.now(ZoneInfo("Asia/Seoul"))
    today_kst = kst_now.date()
    result = await run_with_source_timeout(
        config.id,
        repository,
        config.run_timeout_seconds,
        collect_source(
            config.id,
            adapter,
            repository,
            after_save,
            oldest_published_at=today_kst - timedelta(days=config.filters.max_age_days),
            latest_published_at=today_kst,
            max_items=config.filters.max_items_per_run,
            resume_from_cursor=not refresh_recent,
        ),
    )
    print(f"{result.source_id}: discovered={result.discovered} new={result.new_count} failed={result.failed} cursor={result.cursor_after}")
    return result


def _build_processing_pipeline(
    settings: Settings, schema_path: Path, http: PublicHttpClient
) -> tuple[SourceRepository, Callable[[str, SourceDocument], Awaitable[None]] | None]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return MemorySourceRepository(), None
    repository = PostgresSourceRepository(database_url)
    analysis_schema = json.loads((schema_path.parent / "analysis-result.schema.json").read_text(encoding="utf-8"))
    processor = SourceDocumentProcessor(
        database_url, http, settings.temp_file_dir, settings.max_download_bytes,
        settings.temp_file_ttl_hours, analysis_schema, settings.pdf_processing_attempts,
        settings.pdf_ocr_enabled,
    )
    return repository, processor.process


async def _collect_paths(
    paths: list[Path], schema_path: Path, refresh_recent: bool
) -> CollectBatchSummary:
    settings = Settings.from_environment()
    browser = await _start_shared_browser(paths, schema_path, settings)
    source_slots = asyncio.Semaphore(settings.max_source_concurrency)
    host_slots: defaultdict[str, asyncio.Semaphore] = defaultdict(
        lambda: asyncio.Semaphore(settings.max_sources_per_host)
    )
    try:
        results = await asyncio.gather(
            *[
                _run_limited(
                    path,
                    schema_path,
                    refresh_recent,
                    browser,
                    source_slots,
                    host_slots[_source_host(path, schema_path)],
                )
                for path in paths
            ]
        )
    finally:
        if browser:
            await browser.close()
    failed = sum(r[0] for r in results)
    new_docs = sum(r[1] for r in results)
    discovered = sum(r[2] for r in results)
    return CollectBatchSummary(failed_sources=failed, new_documents_count=new_docs, discovered_count=discovered)


async def _start_shared_browser(
    paths: list[Path], schema_path: Path, settings: Settings
) -> PlaywrightBrowserRenderer | None:
    delays: list[int] = []
    for path in paths:
        try:
            config = load_source_config(path, schema_path)
        except Exception as error:
            print(f"{path.stem}: browser configuration skipped: {error}")
            continue
        if config.adapter.value == "rendered_board":
            delays.append(config.request_delay_ms)
    if not delays or not settings.playwright_enabled:
        return None
    browser = PlaywrightBrowserRenderer(max(delays))
    await browser.start()
    return browser


async def _run_limited(
    path: Path,
    schema_path: Path,
    refresh_recent: bool,
    browser: PlaywrightBrowserRenderer | None,
    source_slots: asyncio.Semaphore,
    host_slot: asyncio.Semaphore,
) -> tuple[int, int, int]:
    async with source_slots, host_slot:
        try:
            res = await run_source(path, schema_path, refresh_recent, browser)
            if isinstance(res, CollectionResult):
                return int(res.failed > 0), res.new_count, res.discovered
            if isinstance(res, (int, float)):
                return int(res > 0), 0, 0
            return 0, 0, 0
        except Exception as error:
            print(f"{path.stem}: initialization failed: {error}")
            return 1, 0, 0


def collect_and_summarize(
    source: str | None,
    all_active: bool,
    config_root: Path,
    schema_path: Path,
    refresh_recent: bool = False,
) -> CollectBatchSummary:
    paths = _source_paths(source, all_active, config_root, schema_path)
    if all_active and (database_url := os.getenv("DATABASE_URL")):
        paths = _filter_database_active_paths(paths, load_active_source_slugs(database_url))
    if not paths or any(not path.exists() for path in paths):
        raise SystemExit("source config not found")
    return asyncio.run(_collect_paths(paths, schema_path, refresh_recent))


def collect_command(
    source: str | None,
    all_active: bool,
    config_root: Path,
    schema_path: Path,
    refresh_recent: bool = False,
) -> int:
    summary = collect_and_summarize(source, all_active, config_root, schema_path, refresh_recent)
    return summary.failed_sources


def _source_paths(source: str | None, all_active: bool, config_root: Path, schema_path: Path) -> list[Path]:
    if not all_active:
        return [config_root / f"{source}.yaml"]
    return [path for path in sorted(config_root.glob("*.yaml")) if load_source_config(path, schema_path).active]


def _source_host(path: Path, schema_path: Path) -> str:
    try:
        return urlparse(str(load_source_config(path, schema_path).list_url)).netloc or path.stem
    except Exception:
        return path.stem


def _filter_database_active_paths(paths: list[Path], active_source_slugs: set[str]) -> list[Path]:
    return [path for path in paths if path.stem in active_source_slugs]
