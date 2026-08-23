from pathlib import Path

import pytest
from report_collector.adapters.sources.kcif.adapter import KcifPublicReportAdapter
from report_collector.adapters.sources.kcmi.adapter import KcmiReportAdapter
from report_collector.adapters.sources.kita.adapter import KitaReportAdapter
from report_collector.adapters.sources.nafi.adapter import NafiResearchAdapter
from report_collector.config.source_config import load_source_config


class FixtureHttp:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    async def fetch_text(self, url: str) -> str:
        return self.pages[url]


async def first(adapter):
    return await anext(adapter.discover(None))


@pytest.mark.asyncio
async def test_kita_maps_public_script_link_to_normal_detail(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kita-report.yaml"))
    detail_url = "https://www.kita.net/researchTrade/report/tradeBrief/tradeBriefDetail.do?no=2976"
    adapter = KitaReportAdapter(config, FixtureHttp({str(config.list_url): (fixture_root / "html/kita-list.html").read_text(encoding="utf-8"), detail_url: "<article>공식 요약</article>"}))  # type: ignore[arg-type]
    item = await first(adapter)
    assert str(item.detail_url) == detail_url
    assert item.published_at.isoformat() == "2026-08-20"


@pytest.mark.asyncio
async def test_kita_uses_public_detail_body_as_summary(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kita-report.yaml"))
    detail_url = "https://www.kita.net/researchTrade/report/tradeBrief/tradeBriefDetail.do?no=2976"
    adapter = KitaReportAdapter(config, FixtureHttp({str(config.list_url): (fixture_root / "html/kita-list.html").read_text(encoding="utf-8"), detail_url: "<div class='detail-body'>공식 본문 요약</div>"}))  # type: ignore[arg-type]
    assert (await adapter.fetch_detail(await first(adapter))).official_summary == "공식 본문 요약"


@pytest.mark.asyncio
async def test_kcmi_maps_public_script_link_to_normal_detail(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kcmi-research.yaml"))
    detail_url = "https://www.kcmi.re.kr/report/report_view?report_no=2315"
    adapter = KcmiReportAdapter(config, FixtureHttp({str(config.list_url): (fixture_root / "html/kcmi-list.html").read_text(encoding="utf-8"), detail_url: "<article>공식 요약</article>"}))  # type: ignore[arg-type]
    assert (await first(adapter)).source_item_key == "2315"


@pytest.mark.asyncio
async def test_nafi_maps_public_script_link_to_normal_detail(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/nafi-research.yaml"))
    detail_url = "https://nafi.re.kr/home/kor/board.do?menuPos=13&act=detail&idx=3588"
    adapter = NafiResearchAdapter(config, FixtureHttp({str(config.list_url): (fixture_root / "html/nafi-list.html").read_text(encoding="utf-8"), detail_url: "<article>공식 요약</article>"}))  # type: ignore[arg-type]
    assert str((await first(adapter)).detail_url) == detail_url


@pytest.mark.asyncio
async def test_nafi_uses_public_contents_as_summary(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/nafi-research.yaml"))
    detail_url = "https://nafi.re.kr/home/kor/board.do?menuPos=13&act=detail&idx=3588"
    adapter = NafiResearchAdapter(config, FixtureHttp({str(config.list_url): (fixture_root / "html/nafi-list.html").read_text(encoding="utf-8"), detail_url: "<main class='contents'>공식 보고서 본문</main>"}))  # type: ignore[arg-type]
    assert (await adapter.fetch_detail(await first(adapter))).official_summary == "공식 보고서 본문"


@pytest.mark.asyncio
async def test_kcif_keeps_public_detail_links_only(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kcif-public-reports.yaml"))
    detail_url = "https://www.kcif.or.kr/finance/financeView?rpt_no=37431"
    adapter = KcifPublicReportAdapter(config, FixtureHttp({str(config.list_url): (fixture_root / "html/kcif-list.html").read_text(encoding="utf-8"), detail_url: "<article>공식 요약</article>"}))  # type: ignore[arg-type]
    assert (await first(adapter)).source_item_key == "37431"
