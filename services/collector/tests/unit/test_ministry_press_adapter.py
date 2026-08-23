from datetime import date

import pytest
from pydantic import HttpUrl
from report_collector.adapters.sources.ministry_press.adapter import MinistryPressAdapter
from report_collector.domain.models import DiscoveredItem, SourceConfig
from report_collector.providers.http.http_client import PublicHttpClient

SAMPLE_LIST_HTML = """
<html>
<body>
  <table>
    <tbody>
      <tr>
        <td class="num">105</td>
        <td class="tit">
          <a href="#" onclick="fn_selectDoc('89123')">
            [보도자료] 국토교통부, 수도권 광역교통망 및 주택공급 확대방안 발표
          </a>
        </td>
        <td class="writer">주택정책과</td>
        <td class="date">2026-08-24</td>
      </tr>
      <tr>
        <td class="num">104</td>
        <td class="tit">
          <a href="#" onclick="fn_selectDoc('89122')">
            [동정] 장관, 현장 간담회 참석 및 격려
          </a>
        </td>
        <td class="writer">홍보담당관</td>
        <td class="date">2026-08-24</td>
      </tr>
      <tr>
        <td class="num">103</td>
        <td class="tit">
          <a href="/news/view?docSeq=89121">
            산업부, 첨단 반도체 특화단지 인프라 지원 강화
          </a>
        </td>
        <td class="writer">산업정책관</td>
        <td class="date">2026-08-23</td>
      </tr>
    </tbody>
  </table>
</body>
</html>
"""

SAMPLE_DETAIL_HTML = """
<html>
<body>
  <div class="view-content">
    <p>국토교통부는 국민 주거 안정을 위해 도심 내 주택 공급을 획기적으로 확대하고 광역교통망을 조기 착공합니다.</p>
  </div>
  <div class="attach">
    <a href="/download/fileDown.do?fileId=9901">20260824_주택공급확대방안.pdf</a>
  </div>
</body>
</html>
"""


@pytest.fixture
def mock_config() -> SourceConfig:
    return SourceConfig(
        id="molit-press",
        name="국토교통부 보도자료",
        adapter="static_board",  # type: ignore[arg-type]
        implementation="report_collector.adapters.sources.ministry_press.adapter:MinistryPressAdapter",
        homepage_url=HttpUrl("https://www.molit.go.kr"),
        list_url=HttpUrl("https://www.molit.go.kr/doc/ko/selectDocList.do?bbsSeq=10"),
        rights_default="LINK_ONLY",  # type: ignore[arg-type]
        content_type="PRESS_RELEASE",  # type: ignore[arg-type]
        poll_interval_minutes=720,
        request_delay_ms=1500,
        timeout_seconds=30,
        run_timeout_seconds=180,
        max_retries=2,
        active=True,
        selectors={"list_item": "tbody tr", "title": "td.tit a", "detail_link": "td.tit a"},
        filters={"exclude_title_keywords": ["동정", "포토", "행사"], "max_age_days": 1, "max_items_per_run": 20},  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_ministry_press_adapter_discovers_and_filters_noise(
    monkeypatch: pytest.MonkeyPatch, mock_config: SourceConfig
) -> None:
    http = PublicHttpClient(timeout=20)

    async def mock_fetch_text(url: str) -> str:
        return SAMPLE_LIST_HTML

    monkeypatch.setattr(http, "fetch_text", mock_fetch_text)

    adapter = MinistryPressAdapter(mock_config, http)
    items = [item async for item in adapter.discover(None)]

    # [동정] item should be filtered out
    assert len(items) == 2
    assert "수도권 광역교통망" in items[0].title
    assert "89123" in str(items[0].detail_url)
    assert items[0].published_at == date(2026, 8, 24)

    assert "첨단 반도체" in items[1].title
    assert "89121" in str(items[1].detail_url)


@pytest.mark.asyncio
async def test_ministry_press_adapter_fetches_detail(
    monkeypatch: pytest.MonkeyPatch, mock_config: SourceConfig
) -> None:
    http = PublicHttpClient(timeout=20)

    async def mock_fetch_text(url: str) -> str:
        return SAMPLE_DETAIL_HTML

    monkeypatch.setattr(http, "fetch_text", mock_fetch_text)

    adapter = MinistryPressAdapter(mock_config, http)

    doc = await adapter.fetch_detail(
        DiscoveredItem(
            source_item_key="doc-89123",
            title="국토부 보도자료",
            detail_url=HttpUrl("https://www.molit.go.kr/doc/ko/selectDoc.do?docSeq=89123"),
            published_at=date(2026, 8, 24),
        )
    )

    assert doc.title == "국토부 보도자료"
    assert doc.institution == "국토교통부 보도자료"
    assert doc.official_summary is not None
    assert "주거 안정을 위해" in doc.official_summary
    assert len(doc.attachments) == 1
    assert doc.attachments[0].declared_type == "PDF"
