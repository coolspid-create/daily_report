from pathlib import Path

import pytest
from pydantic import HttpUrl
from report_collector.adapters.sources.deloitte.adapter import DeloitteInsightsAdapter
from report_collector.config.source_config import load_source_config
from report_collector.domain.models import DiscoveredItem


class FixtureHttp:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.requests: list[str] = []

    async def fetch_text(self, url: str) -> str:
        self.requests.append(url)
        return self.pages.get(url, "<html><body><div>본문 없음</div></body></html>")


SAMPLE_LIST_HTML = """
<!doctype html>
<html lang="ko">
<body>
<main>
  <div>
    <a href="/kr/ko/Industries/financial-services/perspectives/global-fsi-trends-agentic-ai-digital-assets.html">
      이동하는 금융의 패러다임: 에이전틱 AI와 디지털 자산이 바꾸는 미래
    </a>
    <div>2026.08.15</div>
  </div>
  <div>
    <a href="/kr/ko/our-thinking/monthly-trend-tracker/trend-tracker-2026-08.html">
      Deloitte Trend Tracker | 2026년 8월호
    </a>
  </div>
  <div>
    <a href="/kr/ko/our-thinking/deloitte-insights-publications.html">Publication</a>
  </div>
</main>
</body>
</html>
"""

SAMPLE_AI_LIST_HTML = """
<main>
  <article>
    <a href="/kr/ko/issues/generative-ai/ai-use-cases/customer-service.html">
      <h3>생성형 AI 고객 서비스 활용 사례</h3><time>2026.08.21</time>
    </a>
  </article>
  <a href="/kr/ko/issues/generative-ai.html">생성형 AI 허브</a>
</main>
"""

SAMPLE_DETAIL_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta name="publication-date" content="2026-08-15">
</head>
<body>
<header><nav><a href="/">Home</a></nav></header>
<div class="cmp-share-bar__download">
  <a href="/content/dam/assets-shared/docs/industries/financial-services/2026/future-of-insurance.pdf">
    보험 2035의 미래
  </a>
</div>
<main>
  <article>
    <h2>에이전틱 AI와 디지털 금융의 융합</h2>
    <p>금융 산업은 생성형 AI에서 더 나아가 스스로 판단하고 실행하는 에이전틱 AI 중심으로 빠르게 전환하고 있습니다.</p>
    <p>글로벌 금융기관들은 디지털 자산 커스터디와 토큰화 기술을 결합하여 새로운 비즈니스 모델을 창출하고 있습니다.</p>
    <div class="downloads">
      <a href="/content/dam/assets-zone1/kr/ko/docs/industries/financial-services/2026/2026-fsi-predictions.pdf#page=1">
        리포트 다운로드 PDF
      </a>
    </div>
  </article>
</main>
<footer><p>&copy; 2026 Deloitte</p></footer>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_deloitte_adapter_discover() -> None:
    config = load_source_config(Path("config/sources/deloitte-insights.yaml"))
    collection_urls = [str(url) for url in config.collection_urls]
    pages = {url: "<main></main>" for url in collection_urls}
    pages[collection_urls[0]] = SAMPLE_LIST_HTML
    pages[collection_urls[3]] = SAMPLE_AI_LIST_HTML
    http = FixtureHttp(pages)
    adapter = DeloitteInsightsAdapter(config, http)  # type: ignore[arg-type]

    items = [it async for it in adapter.discover(None)]
    assert len(items) == 3
    assert items[0].title == "이동하는 금융의 패러다임: 에이전틱 AI와 디지털 자산이 바꾸는 미래"
    assert "global-fsi-trends" in items[0].source_item_key
    assert items[0].published_at.isoformat() == "2026-08-15"
    assert items[1].published_at is None
    assert items[2].title == "생성형 AI 고객 서비스 활용 사례"
    assert set(http.requests) == set(collection_urls)
    assert all("deloitte-insights.html" not in str(item.detail_url) for item in items)


@pytest.mark.asyncio
async def test_deloitte_adapter_fetch_detail() -> None:
    config = load_source_config(Path("config/sources/deloitte-insights.yaml"))
    detail_url = "https://www.deloitte.com/kr/ko/Industries/financial-services/perspectives/global-fsi-trends-agentic-ai-digital-assets.html"
    http = FixtureHttp({str(config.list_url): SAMPLE_LIST_HTML, detail_url: SAMPLE_DETAIL_HTML})
    adapter = DeloitteInsightsAdapter(config, http)  # type: ignore[arg-type]

    item = DiscoveredItem(
        source_item_key="test-key",
        title="이동하는 금융의 패러다임: 에이전틱 AI와 디지털 자산이 바꾸는 미래",
        detail_url=HttpUrl(detail_url),
        published_at=None,
    )
    doc = await adapter.fetch_detail(item)
    assert doc.title == item.title
    assert "에이전틱 AI" in (doc.official_summary or "")
    assert doc.published_at.isoformat() == "2026-08-15"
    assert len(doc.attachments) == 1
    assert "2026-fsi-predictions.pdf" in str(doc.attachments[0].url)
    assert "future-of-insurance.pdf" not in str(doc.attachments[0].url)
    assert doc.attachments[0].declared_type == "application/pdf"
    assert doc.rights_status.value == "LINK_ONLY"
