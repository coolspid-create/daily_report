from pathlib import Path

import pytest
from report_collector.adapters.sources.public_research.adapter import PublicResearchAdapter
from report_collector.config.source_config import load_source_config
from report_collector.providers.http.http_client import _decode_text


class FixtureHttp:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    async def fetch_text(self, url: str) -> str:
        return self.pages[url]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config_name", "html", "expected_key", "url_fragment"),
    [
        ("posri-research", "<p class='h_1'><a href='bbs_view.do?num=9018'>AI 시대, R&D 대혁명</a></p>", "9018", "num=9018"),
        ("hri-research", "<a class='item' href='/kor/report/view/97831'><span class='tit-text'>물가 안정 전망</span></a>", "97831", "/kor/report/view/97831"),
        ("wfri-research", "<li><a href='/ko/web/report.php?idx=2605&page_type=view'><span class='report-item__title'>금융시장 브리프</span></a></li>", "2605", "idx=2605"),
        ("fki-report", "<li><a class='subject' href=\"javascript:detailNT('00036221')\">기업 정책 보고서</a></li>", "00036221", "bbs_id=00036221"),
        ("keri-research", "<div class='list_item'><div class='item_name' onclick=\"javascript:detailNT('00036204')\">경제 연구</div></div>", "00036204", "bbs_id=00036204"),
        ("ifans-focus", "<li><a onclick=\"fnCmdView('14830','P07');return false;\">외교안보 분석</a></li>", "14830", "pblctDtaSn=14830"),
    ],
)
async def test_public_research_sources_map_to_official_detail(
    config_name: str, html: str, expected_key: str, url_fragment: str
) -> None:
    config = load_source_config(Path(f"config/sources/{config_name}.yaml"))
    adapter = PublicResearchAdapter(config, FixtureHttp({str(config.list_url): html}))  # type: ignore[arg-type]

    item = await anext(adapter.discover(None))

    assert item.source_item_key == expected_key
    assert url_fragment in str(item.detail_url)


@pytest.mark.asyncio
async def test_public_research_keeps_only_normal_or_official_file_links() -> None:
    config = load_source_config(Path("config/sources/fki-report.yaml"))
    list_html = "<li><a class='subject' href=\"javascript:detailNT('00036221')\">기업 정책 보고서</a></li>"
    detail_url = "https://www.fki.or.kr/kor/publication/report_detail.do?bbs_id=00036221&category=RE&pageIndex=1"
    detail_html = "<article>공식 페이지 요약</article><button onclick=\"fileDown('123','1')\">다운로드</button>"
    adapter = PublicResearchAdapter(config, FixtureHttp({str(config.list_url): list_html, detail_url: detail_html}))  # type: ignore[arg-type]

    document = await adapter.fetch_detail(await anext(adapter.discover(None)))

    assert document.official_summary == "공식 페이지 요약"
    assert str(document.attachments[0].url).endswith("file_seq=123&file_sn=1")


def test_public_http_decodes_euc_kr_html() -> None:
    assert _decode_text("공식 연구자료".encode("euc-kr"), "text/html; charset=euc-kr") == "공식 연구자료"
