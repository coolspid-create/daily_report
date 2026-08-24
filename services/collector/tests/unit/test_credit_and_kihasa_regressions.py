from pathlib import Path

import pytest
from report_collector.adapters.sources.credit_rating.adapter import CreditRatingAdapter
from report_collector.adapters.sources.kihasa.adapter import KihasaAdapter
from report_collector.config.source_config import load_source_config


class FixtureHttp:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    async def fetch_text(self, url: str) -> str:
        return self.pages.get(url, "<html><body><div>본문 없음</div></body></html>")


async def first(adapter):
    return await anext(adapter.discover(None))


@pytest.mark.asyncio
async def test_nice_credit_rating_adapter(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/nice-credit-research.yaml"))
    list_html = (fixture_root / "html/nice-list.html").read_text(encoding="utf-8")
    adapter = CreditRatingAdapter(config, FixtureHttp({str(config.list_url): list_html}))  # type: ignore[arg-type]

    item = await first(adapter)
    assert item.title == "2026 하반기 신용등급 변동요인 및 산업별 전망"
    assert item.source_item_key == "1024"
    assert item.published_at.isoformat() == "2026-08-22"

    document = await adapter.fetch_detail(item)
    assert document.title == item.title
    assert document.rights_status.value == "LINK_ONLY"
    assert document.attachments == []


@pytest.mark.asyncio
async def test_nice_credit_rating_preview_links() -> None:
    config = load_source_config(Path("config/sources/nice-credit-research.yaml"))
    html = """
    <table><tbody>
      <tr>
        <td><a href="javascript:research_common.fn_preview('H26536')">SK하이닉스 자기주식 취득·소각계획과 확대된 주주환원계획 발표</a></td>
        <td>이예리</td>
        <td>2026.08.20</td>
      </tr>
    </tbody></table>
    """
    detail_html = """
    <div class="pop-conts"><div class="noticeContents">[코멘트] SK하이닉스 자기주식 취득 및 주주환원계획 분석</div></div>
    """
    preview_url = "https://www.nicerating.com/research/preview.do?fileId=H26536"
    adapter = CreditRatingAdapter(config, FixtureHttp({str(config.list_url): html, preview_url: detail_html}))  # type: ignore[arg-type]

    item = await first(adapter)
    assert item.source_item_key == "H26536"
    assert str(item.detail_url) == preview_url
    assert item.published_at.isoformat() == "2026-08-20"

    document = await adapter.fetch_detail(item)
    assert document.rights_status.value == "LINK_ONLY"
    assert "SK하이닉스" in (document.official_summary or "")


@pytest.mark.asyncio
async def test_korea_ratings_adapter(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/korea-ratings-research.yaml"))
    list_html = (fixture_root / "html/korea-ratings-list.html").read_text(encoding="utf-8")
    adapter = CreditRatingAdapter(config, FixtureHttp({str(config.list_url): list_html}))  # type: ignore[arg-type]

    item = await first(adapter)
    assert item.title == "석유화학 업종 신용도 하방압력 점검"
    assert item.source_item_key == "8899"
    assert item.published_at.isoformat() == "2026-08-22"

    document = await adapter.fetch_detail(item)
    assert document.rights_status.value == "LINK_ONLY"
    assert document.attachments == []


@pytest.mark.asyncio
async def test_kis_rating_adapter(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kis-rating-research.yaml"))
    list_html = (fixture_root / "html/kis-rating-list.html").read_text(encoding="utf-8")
    adapter = CreditRatingAdapter(config, FixtureHttp({str(config.list_url): list_html}))  # type: ignore[arg-type]

    item = await first(adapter)
    assert item.title == "건설업 유동성 리스크 및 재무구조 점검"
    assert item.source_item_key == "5544"
    assert item.published_at.isoformat() == "2026-08-22"

    document = await adapter.fetch_detail(item)
    assert document.rights_status.value == "LINK_ONLY"
    assert document.attachments == []


@pytest.mark.asyncio
async def test_kihasa_2step_precise_date_extraction(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kihasa-research.yaml"))
    list_html = (fixture_root / "html/kihasa-list.html").read_text(encoding="utf-8")
    detail_url = "https://www.kihasa.re.kr/publish/report/view?type=research&seq=74916"
    detail_html = (fixture_root / "html/kihasa-detail.html").read_text(encoding="utf-8")

    adapter = KihasaAdapter(
        config,
        FixtureHttp({str(config.list_url): list_html, detail_url: detail_html}),  # type: ignore[arg-type]
    )

    item = await first(adapter)
    assert item.source_item_key == "74916"
    assert str(item.detail_url) == detail_url

    document = await adapter.fetch_detail(item)
    assert document.published_at.isoformat() == "2026-08-22"
    assert "인구구조 변화" in (document.official_summary or "")
