from pathlib import Path

import pytest
from report_collector.adapters.factory import build_adapter
from report_collector.config.source_config import load_source_config
from report_collector.providers.browser.playwright_browser import PlaywrightBrowserRenderer
from report_collector.providers.http.http_client import PublicHttpClient

SOURCE_IDS = (
    "nars",
    "kdi-research",
    "bok-rss",
    "kihasa-research",
    "krihs-research",
    "kiep-research",
    "kei-research",
    "kiet-research",
    "kedi-research",
    "keei-research",
    "kinu-research",
    "kipf-research",
    "inss-issue-brief",
    "kistep-research",
    "kistep-brief",
    "kisdi-policy",
    "kisdi-stat",
    "nabo-analysis",
    "nabo-brief",
    "koti-research",
    "koti-brief",
    "kif-financial-brief",
    "kif-research",
)
ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize("source_id", SOURCE_IDS)
async def test_first_live_source_item(source_id: str) -> None:
    config = load_source_config(
        ROOT / f"config/sources/{source_id}.yaml",
        ROOT / "contracts/source-config.schema.json",
    )
    http = PublicHttpClient(config.timeout_seconds, 0, config.request_delay_ms)
    browser = (
        PlaywrightBrowserRenderer(config.request_delay_ms)
        if config.adapter.value == "rendered_board"
        else None
    )
    adapter = build_adapter(config, http, browser)
    first = None
    async for item in adapter.discover(None):
        first = item
        break
    assert first is not None
    detail = await adapter.fetch_detail(first)
    assert detail.title
    assert str(detail.detail_url).startswith("https://")
