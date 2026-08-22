from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from report_collector.adapters.generic.static_board import StaticBoardAdapter
from report_collector.adapters.sources.bok.adapter import BokRssAdapter
from report_collector.adapters.sources.fsc.adapter import FinancialServicesCommissionAdapter
from report_collector.adapters.sources.fsc.adapter import _date as fsc_date
from report_collector.adapters.sources.fsc.adapter import _summary as fsc_summary
from report_collector.adapters.sources.hana.adapter import HanaResearchAdapter
from report_collector.adapters.sources.hana.adapter import _date as hana_date
from report_collector.adapters.sources.inss.adapter import InssAdapter
from report_collector.adapters.sources.kb.adapter import KbResearchAdapter
from report_collector.adapters.sources.kdi.adapter import KdiRenderedAdapter
from report_collector.adapters.sources.kedi.adapter import KediAdapter
from report_collector.adapters.sources.keis.adapter import KeisResearchAdapter
from report_collector.adapters.sources.kipf.adapter import KipfAdapter
from report_collector.adapters.sources.kli.adapter import KliAdapter
from report_collector.adapters.sources.kmi.adapter import KmiResearchAdapter
from report_collector.adapters.sources.kotra.adapter import KotraMarketNewsAdapter
from report_collector.adapters.sources.krihs.adapter import KrihsAdapter
from report_collector.adapters.sources.mof.adapter import MinistryOfOceansAdapter
from report_collector.adapters.sources.nars.adapter import NarsAdapter
from report_collector.adapters.sources.nars.adapter import _date as nars_date
from report_collector.adapters.sources.stepi.adapter import StepiAdapter
from report_collector.config.source_config import load_source_config


class FixtureHttp:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    async def fetch_text(self, url: str) -> str:
        return self.pages[url]


class FixtureBrowser:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    async def render(self, url: str, wait_for: str | None, timeout_ms: int) -> str:
        return self.pages[url]


class FixtureFormBrowser(FixtureBrowser):
    def __init__(self, pages: dict[str, str], detail_html: str) -> None:
        super().__init__(pages)
        self.detail_html = detail_html
        self.submissions: list[tuple[str, str, dict[str, str], str]] = []

    async def submit_form(
        self,
        url: str,
        form_selector: str,
        fields: dict[str, str],
        action: str,
        wait_for: str | None,
        timeout_ms: int,
    ) -> str:
        self.submissions.append((url, form_selector, fields, action))
        return self.detail_html


async def first(adapter):
    return await anext(adapter.discover(None))


@pytest.mark.asyncio
async def test_nars_fixture(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/nars.yaml"))
    item_url = "https://www.nars.go.kr/report/view.do?brdSeq=49538&cmsCode=CM0043"
    pages = {
        str(config.list_url): (fixture_root / "html/nars-list.html").read_text(encoding="utf-8"),
        item_url: (fixture_root / "html/nars-detail.html").read_text(encoding="utf-8"),
    }
    adapter = NarsAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    item = await first(adapter)
    detail = await adapter.fetch_detail(item)
    assert item.source_item_key == "49538"
    assert "fileDownload2.do" in str(detail.attachments[0].url)


@pytest.mark.asyncio
async def test_kdi_rendered_fixture(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kdi-research.yaml"))
    item_url = "https://www.kdi.re.kr/research/reportView?pub_no=19217"
    pages = {
        str(config.list_url): (fixture_root / "html/kdi-list.html").read_text(encoding="utf-8"),
        item_url: (fixture_root / "html/kdi-detail.html").read_text(encoding="utf-8"),
    }
    adapter = KdiRenderedAdapter(config, FixtureHttp({}), FixtureBrowser(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2025-12-31"
    assert "/file/download?" in str(detail.attachments[0].url)


@pytest.mark.asyncio
async def test_krihs_fixture_uses_official_detail_page(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/krihs-research.yaml"))
    item_url = "https://library.krihs.re.kr/library/10120/contents/7798930"
    pages = {
        str(config.list_url): (fixture_root / "html/krihs-list.html").read_text(encoding="utf-8"),
        item_url: (fixture_root / "html/krihs-detail.html").read_text(encoding="utf-8"),
    }
    adapter = KrihsAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-03-31"
    assert detail.attachments == []
    assert "분산형 공간구조" in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_kiep_fixture_reads_official_summary(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kiep-research.yaml"))
    detail_url = "https://www.kiep.go.kr/gallery.es?mid=a10101020000&bid=0001&act=view&list_no=12535"
    pages = {
        str(config.list_url): (fixture_root / "html/kiep-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kiep-detail.html").read_text(encoding="utf-8"),
    }
    adapter = StaticBoardAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-07-21"
    assert detail.official_summary is not None
    assert detail.attachments == []


@pytest.mark.asyncio
async def test_stepi_fixture_reads_public_summary(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/stepi-research.yaml"))
    detail_url = "https://www.stepi.re.kr/site/stepiko/report/View.do?cateCont=A0206&reIdx=86"
    pages = {
        str(config.list_url): (fixture_root / "html/stepi-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/stepi-detail.html").read_text(encoding="utf-8"),
    }
    adapter = StepiAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-07-15"
    assert "적정성을 검토" in (detail.official_summary or "")
    assert detail.attachments == []


@pytest.mark.asyncio
async def test_kedi_fixture_submits_official_public_form(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kedi-research.yaml"))
    browser = FixtureFormBrowser(
        {str(config.list_url): (fixture_root / "html/kedi-list.html").read_text(encoding="utf-8")},
        (fixture_root / "html/kedi-detail.html").read_text(encoding="utf-8"),
    )
    adapter = KediAdapter(config, FixtureHttp({}), browser)  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert browser.submissions[0][2] == {"plNum0": "16539"}
    assert detail.published_at.isoformat() == "2026-08-21"
    assert "개선 과제" in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_kipf_fixture_submits_official_public_form(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kipf-research.yaml"))
    browser = FixtureFormBrowser(
        {str(config.list_url): (fixture_root / "html/kipf-list.html").read_text(encoding="utf-8")},
        (fixture_root / "html/kipf-detail.html").read_text(encoding="utf-8"),
    )
    adapter = KipfAdapter(config, FixtureHttp({}), browser)  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert browser.submissions[0][2] == {"serialNo": "527614"}
    assert detail.published_at.isoformat() == "2026-08-01"
    assert detail.official_summary is None


@pytest.mark.asyncio
async def test_kli_license_error_is_reported_without_bypass(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kli-research.yaml"))
    adapter = KliAdapter(
        config,
        FixtureHttp(
            {
                str(config.list_url): (fixture_root / "html/kli-license-error.html").read_text(
                    encoding="utf-8"
                )
            }
        ),
    )  # type: ignore[arg-type]
    health = await adapter.health_check()
    assert not health.healthy
    assert health.message == "public page license error"


@pytest.mark.asyncio
async def test_bok_official_rss_fixture(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/bok-rss.yaml"))
    detail_url = "https://www.bok.or.kr/portal/bbs/P0002353/view.do?nttId=11063845"
    pages = {
        str(config.list_url): (fixture_root / "rss/bok.xml").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/bok-detail.html").read_text(encoding="utf-8"),
    }
    adapter = BokRssAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.source_item_key == "bok-2026-19"
    assert detail.attachments[0].declared_type == "application/pdf"
    assert "청년고용" in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_inss_fixture_reads_public_abstract_and_direct_file(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/inss-issue-brief.yaml"))
    detail_url = "https://www.inss.re.kr/publication/bbs/ib_view.do?bbsId=ib&nttId=41038007"
    pages = {
        str(config.list_url): (fixture_root / "html/inss-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/inss-detail.html").read_text(encoding="utf-8"),
    }
    adapter = InssAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-08-20"
    assert "/common/download.do?" in str(detail.attachments[0].url)
    assert "한국 외교" in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_kotra_fixture_reads_public_detail_and_official_file(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kotra-market-news.yaml"))
    detail_url = "https://dream.kotra.or.kr/kotranews/cms/news/actionKotraBoardDetail.do?SITE_NO=3&MENU_ID=180&pNttSn=243526"
    pages = {
        str(config.list_url): (fixture_root / "html/kotra-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kotra-detail.html").read_text(encoding="utf-8"),
    }
    adapter = KotraMarketNewsAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-08-20"
    assert "fileDown.do" in str(detail.attachments[0].url)
    assert "탈탄소 규제" in (detail.official_summary or "")
    assert "첨부파일" not in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_keis_fixture_uses_public_detail_parameters(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/keis-research.yaml"))
    detail_url = "https://www.keis.or.kr/keis/ko/proj/113/pblc/detail.do?categoryIdx=131&pubIdx=11352"
    pages = {
        str(config.list_url): (fixture_root / "html/keis-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/keis-detail.html").read_text(encoding="utf-8"),
    }
    adapter = KeisResearchAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-08-14"
    assert "/cmmn/download.do?" in str(detail.attachments[0].url)


@pytest.mark.asyncio
async def test_fsc_fixture_reads_policy_page_and_file(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/fsc-policy.yaml"))
    detail_url = "https://www.fsc.go.kr/no010101/87572?curPage=1"
    pages = {
        str(config.list_url): (fixture_root / "html/fsc-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/fsc-detail.html").read_text(encoding="utf-8"),
    }
    adapter = FinancialServicesCommissionAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-08-20"
    assert "/comm/getFile?" in str(detail.attachments[0].url)


@pytest.mark.asyncio
async def test_kb_fixture_maps_public_download_function(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kb-research.yaml"))
    detail_url = "https://www.kbfg.com/kbresearch/report/reportView.do?reportId=2001342"
    pages = {
        str(config.list_url): (fixture_root / "html/kb-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kb-detail.html").read_text(encoding="utf-8"),
    }
    adapter = KbResearchAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-08-18"
    assert "FileDown.do?atchFileId=FILE_000000002001564" in str(detail.attachments[0].url)


@pytest.mark.asyncio
async def test_kmi_fixture_reads_public_html_and_official_viewer(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kmi-research.yaml"))
    detail_url = "https://www.kmi.re.kr/web/board/view.do?rbsIdx=384&idx=1335"
    pages = {
        str(config.list_url): (fixture_root / "html/kmi-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kmi-detail.html").read_text(encoding="utf-8"),
    }
    adapter = KmiResearchAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-08-08"
    assert "viewer.do" in str(detail.attachments[0].url)


@pytest.mark.asyncio
async def test_hana_fixture_maps_public_download(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/hana-research.yaml"))
    detail_url = "https://www.hanaif.re.kr/boardDetail.do?hmpeSeqNo=37026"
    pages = {
        str(config.list_url): (fixture_root / "html/hana-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/hana-detail.html").read_text(encoding="utf-8"),
    }
    detail = await HanaResearchAdapter(config, FixtureHttp(pages)).fetch_detail(
        await first(HanaResearchAdapter(config, FixtureHttp(pages)))
    )  # type: ignore[arg-type]
    assert detail.published_at.isoformat() == "2026-08-21"
    assert "hanaifFileDownload.jsp?seq=103308" in str(detail.attachments[0].url)


@pytest.mark.asyncio
async def test_mof_fixture_maps_public_detail_and_pdf(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/mof-press.yaml"))
    detail_url = "https://www.mof.go.kr/doc/ko/selectDoc.do?docSeq=68110&menuSeq=971&bbsSeq=10"
    pages = {
        str(config.list_url): (fixture_root / "html/mof-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/mof-detail.html").read_text(encoding="utf-8"),
    }
    adapter = MinistryOfOceansAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail(await first(adapter))
    assert detail.published_at.isoformat() == "2026-08-20"
    assert "readDownloadFile.do" in str(detail.attachments[0].url)


@pytest.mark.parametrize("parser", [fsc_date, hana_date, nars_date])
def test_source_dates_accept_one_digit_and_korean_date_formats(
    parser: Callable[[str], date | None],
) -> None:
    assert parser("등록일 2026년 8월 2일") == date(2026, 8, 2)
    assert parser("2026.8.2") == date(2026, 8, 2)


def test_fsc_summary_is_limited_to_document_schema_length() -> None:
    soup = BeautifulSoup(f"<div class='view-cont'>{'summary ' * 1_000}</div>", "html.parser")

    summary = fsc_summary(soup)

    assert summary is not None
    assert len(summary) <= 3_000
