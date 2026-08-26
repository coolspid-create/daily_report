from pathlib import Path

import pytest
from report_collector.adapters.sources.ibks.adapter import IbksResearchAdapter
from report_collector.adapters.sources.pwc.adapter import SamilPwcAdapter
from report_collector.adapters.sources.telegram_research.adapter import (
    OfficialTelegramResearchAdapter,
    _extract_title,
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
    assert str(item.detail_url) == "https://t.me/KiwoomResearch/10"
    assert adapter.report_urls[item.source_item_key].startswith("https://bbn.kiwoom.com/")


def test_official_channel_orders_newest_post_first() -> None:
    config = load_source_config(Path("config/sources/kiwoom-research.yaml"))
    adapter = OfficialTelegramResearchAdapter(config, FixtureHttp())  # type: ignore[arg-type]
    html = """
    <div class="tgme_widget_message" data-post="KiwoomResearch/10">
      <div class="tgme_widget_message_text">예전 자료 <a href="https://bbn.kiwoom.com/rfCR10">PDF</a></div>
      <time datetime="2026-08-25T01:00:00+00:00"></time>
    </div>
    <div class="tgme_widget_message" data-post="KiwoomResearch/11">
      <div class="tgme_widget_message_text">최신 자료 <a href="https://bbn.kiwoom.com/rfCR11">PDF</a></div>
      <time datetime="2026-08-25T02:00:00+00:00"></time>
    </div>
    """
    assert adapter._parse_messages(html)[0][0].source_item_key == "KiwoomResearch-11"


def test_official_channel_extracts_titles_without_body_copy() -> None:
    assert _extract_title(
        """[SK증권 최관순, 한동희, 황지우]
대환원의 시대 (요약)
1. 대규모 현금이 주주환원에 나선다.
2. 추가 내용"""
    ) == "[SK증권 최관순, 한동희, 황지우] 대환원의 시대"
    assert _extract_title(
        """이번 자료는 저희 리서치센터 유틸리티 담당 자료입니다.
많은 관심 부탁드립니다!
▶️
보고서:
https://bbn.kiwoom.com/rfBC1234
아래 내용은 보고서 중 건설 부문 요약입니다.
♣️
건설/유틸리티 산업 인덱스 자료
[키움 건설 신대현]
♣️
건설/유틸리티: 데이터센터가 불러올 파급효과
1) 산업 설명"""
    ) == "[키움 건설 신대현] 건설/유틸리티: 데이터센터가 불러올 파급효과"
    assert _extract_title(
        """[SK증권 화장품/의류 형권훈]
(
kh.hyung@sks.co.kr/3773-9997
)
▶️
Weekly Amazon Beauty Check
- K뷰티 유니버스 주간 요약"""
    ) == "[SK증권 화장품/의류 형권훈] Weekly Amazon Beauty Check"
    assert _extract_title(
        """[SK 증권 원유승][8월 금통위 프리뷰] 동결 전망. 안정적인 기대 인플레와 환율
- 8월 금통위, 기준금리 동결 전망
- 10월 추가 인상 전망"""
    ) == "[SK 증권 원유승][8월 금통위 프리뷰] 동결 전망. 안정적인 기대 인플레와 환율"
    assert _extract_title(
        """[SK증권 미래산업/미드스몰캡] Analyst 나승두
(nsdoo@sks.co.kr/3773-8891)
중소형주, 돈 잘 벌고 있는 코스닥
- Signal: 1H26 영업이익 증가"""
    ) == "[SK증권 미래산업/미드스몰캡] 중소형주, 돈 잘 벌고 있는 코스닥"


@pytest.mark.asyncio
async def test_official_channel_keeps_source_page_separate_from_pdf() -> None:
    config = load_source_config(Path("config/sources/kiwoom-research.yaml"))
    adapter = OfficialTelegramResearchAdapter(config, FixtureHttp())  # type: ignore[arg-type]
    html = """
    <div class="tgme_widget_message" data-post="KiwoomResearch/11">
      <div class="tgme_widget_message_text">[키움 ETF 김진영]<br>New ETF Line-Up
        <a href="https://bbn.kiwoom.com/rfCR456">PDF</a>
      </div>
      <time datetime="2026-08-25T22:00:00+00:00"></time>
    </div>
    """
    item, _ = adapter._parse_messages(html)[0]
    detail = await adapter.fetch_detail(item)
    assert item.title == "[키움 ETF 김진영] New ETF Line-Up"
    assert str(detail.detail_url) == "https://t.me/KiwoomResearch/11"
    assert str(detail.attachments[0].url) == "https://bbn.kiwoom.com/rfCR456"


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
    detail = await adapter.fetch_detail(item)
    assert "m.ibks.com/iko/IKO01/download.do" in str(detail.attachments[0].url)
    assert detail.detail_url == detail.attachments[0].url
