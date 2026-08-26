from pathlib import Path

import pytest
from report_collector.adapters.sources.ibks.adapter import IbksResearchAdapter
from report_collector.adapters.sources.pwc.adapter import SamilPwcAdapter
from report_collector.adapters.sources.telegram_research.adapter import (
    OfficialTelegramResearchAdapter,
)
from report_collector.config.source_config import load_source_config


class FixtureHttp:
    async def fetch_text(self, url: str) -> str:
        return ""


class FixtureBrowser:
    def __init__(self, html: str) -> None:
        self.html = html

    async def render(self, url: str, wait_for: str | None, timeout_ms: int) -> str:
        return self.html


def test_pwc_collection_metadata_uses_exact_publication_date() -> None:
    config = load_source_config(Path("config/sources/samil-pwc-insights.yaml"))
    adapter = SamilPwcAdapter(config, FixtureHttp())  # type: ignore[arg-type]
    html = """
    {&quot;date&quot;:&quot;Tue Aug 25 00:00:00 UTC 2026&quot;,
     &quot;title&quot;:&quot;AI 시대 산업 보고서 | 삼일PwC&quot;,
     &quot;url&quot;:&quot;https://www.pwc.com/kr/ko/insights/issue-brief/ai-report.html&quot;}
    """
    item = adapter._parse_list(html)[0]
    assert item.published_at.isoformat() == "2026-08-25"
    assert item.title == "AI 시대 산업 보고서"


def test_official_channel_only_selects_kiwoom_report_links() -> None:
    config = load_source_config(Path("config/sources/kiwoom-research.yaml"))
    adapter = OfficialTelegramResearchAdapter(config, FixtureHttp())  # type: ignore[arg-type]
    html = """
    <div class="tgme_widget_message" data-post="KiwoomResearch/10">
      <div class="tgme_widget_message_text">키움 리포트
        <a href="https://example.com/news">뉴스</a>
        <a href="http://bbn.kiwoom.com/rfCR123">보고서</a>
      </div>
      <time datetime="2026-08-25T22:00:00+00:00"></time>
    </div>
    """
    item, _ = adapter._parse_messages(html)[0]
    assert item.source_item_key == "KiwoomResearch-10"
    assert item.published_at.isoformat() == "2026-08-26"
    assert str(item.detail_url).startswith("https://bbn.kiwoom.com/")


@pytest.mark.asyncio
async def test_ibks_rendered_list_reads_span_date_and_official_download() -> None:
    config = load_source_config(Path("config/sources/ibks-research.yaml"))
    html = """
    <ul><li>
      <a class="text"><p class="tit">IBKS Daily</p><p><span class="date">2026.08.26</span></p></a>
      <a class="down" href="/iko/IKO01/download.do?seq=16917&amp;gubun=DAIL">파일</a>
    </li></ul>
    """
    adapter = IbksResearchAdapter(
        config,
        FixtureHttp(),  # type: ignore[arg-type]
        FixtureBrowser(html),  # type: ignore[arg-type]
    )
    item = (await adapter._items())[0]
    assert item.source_item_key == "ibks-16917"
    assert item.published_at.isoformat() == "2026-08-26"
    assert "m.ibks.com/iko/IKO01/download.do" in str(item.detail_url)
