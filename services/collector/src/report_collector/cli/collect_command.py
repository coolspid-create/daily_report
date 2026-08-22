import asyncio
import json
import os
from datetime import date, timedelta
from pathlib import Path

from report_collector.adapters.factory import build_adapter
from report_collector.config.settings import Settings
from report_collector.config.source_config import load_source_config
from report_collector.pipelines.collect_source import collect_source
from report_collector.pipelines.process_source_document import SourceDocumentProcessor
from report_collector.pipelines.source_run_guard import run_with_source_timeout
from report_collector.providers.browser.playwright_browser import PlaywrightBrowserRenderer
from report_collector.providers.http.http_client import PublicHttpClient
from report_collector.repositories.source_repository import MemorySourceRepository, SourceRepository
from report_collector.repositories.supabase.postgres_source_repository import (
    PostgresSourceRepository,
    load_active_source_slugs,
)


async def run_source(config_path: Path, schema_path: Path, refresh_recent: bool = False) -> int:
    config = load_source_config(config_path, schema_path)
    settings = Settings.from_environment()
    http = PublicHttpClient(config.timeout_seconds, config.max_retries, config.request_delay_ms)
    browser = (
        PlaywrightBrowserRenderer(config.request_delay_ms)
        if config.adapter.value == "rendered_board" and settings.playwright_enabled
        else None
    )
    adapter = build_adapter(config, http, browser)
    database_url = os.getenv("DATABASE_URL")
    repository: SourceRepository
    after_save = None
    if database_url:
        repository = PostgresSourceRepository(database_url)
        analysis_schema = json.loads(
            (schema_path.parent / "analysis-result.schema.json").read_text(encoding="utf-8")
        )
        processor = SourceDocumentProcessor(
            database_url,
            http,
            settings.temp_file_dir,
            settings.max_download_bytes,
            settings.temp_file_ttl_hours,
            analysis_schema,
            settings.pdf_processing_attempts,
            settings.pdf_ocr_enabled,
        )
        after_save = processor.process
    else:
        repository = MemorySourceRepository()
    result = await run_with_source_timeout(
        config.id,
        repository,
        config.run_timeout_seconds,
        collect_source(
            config.id,
            adapter,
            repository,
            after_save,
            oldest_published_at=date.today() - timedelta(days=config.filters.max_age_days),
            latest_published_at=date.today(),
            max_items=config.filters.max_items_per_run,
            resume_from_cursor=not refresh_recent,
        ),
    )
    print(
        f"{result.source_id}: discovered={result.discovered} failed={result.failed} cursor={result.cursor_after}"
    )
    return result.failed


def collect_command(
    source: str | None,
    all_active: bool,
    config_root: Path,
    schema_path: Path,
    refresh_recent: bool = False,
) -> int:
    paths = _source_paths(source, all_active, config_root, schema_path)
    if all_active and (database_url := os.getenv("DATABASE_URL")):
        paths = _filter_database_active_paths(paths, load_active_source_slugs(database_url))
    if not paths or any(not path.exists() for path in paths):
        raise SystemExit("source config not found")
    failed_sources = 0
    for path in paths:
        try:
            failed_sources += int(asyncio.run(run_source(path, schema_path, refresh_recent)) > 0)
        except Exception as error:
            print(f"{path.stem}: initialization failed: {error}")
            failed_sources += 1
    return failed_sources


def _source_paths(
    source: str | None, all_active: bool, config_root: Path, schema_path: Path
) -> list[Path]:
    if not all_active:
        return [config_root / f"{source}.yaml"]
    return [
        path
        for path in sorted(config_root.glob("*.yaml"))
        if load_source_config(path, schema_path).active
    ]


def _filter_database_active_paths(paths: list[Path], active_source_slugs: set[str]) -> list[Path]:
    return [path for path in paths if path.stem in active_source_slugs]
