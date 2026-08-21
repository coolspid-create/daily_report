from pathlib import Path

import pytest
from report_collector.adapters.generic.html_parser import _date
from report_collector.adapters.generic.rendered_board import RenderedBoardAdapter
from report_collector.adapters.generic.static_board import StaticBoardAdapter
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


async def discovered(adapter: StaticBoardAdapter | RenderedBoardAdapter) -> list:
    return [item async for item in adapter.discover(None)]


@pytest.mark.asyncio
async def test_static_adapter_list_detail(fixture_root: Path) -> None:
    config = load_source_config(fixture_root / "config/sample-static.yaml")
    pages = {
        str(config.list_url): (fixture_root / "html/sample-static-list.html").read_text(
            encoding="utf-8"
        ),
        "https://fixtures.example/reports/102": (
            fixture_root / "html/sample-static-detail.html"
        ).read_text(encoding="utf-8"),
    }
    adapter = StaticBoardAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    items = await discovered(adapter)
    assert [item.source_item_key for item in items] == ["s-102", "s-101"]
    detail = await adapter.fetch_detail(items[0])
    assert detail.rights_status.value == "LINK_ONLY"
    assert str(detail.attachments[0].url) == "https://fixtures.example/files/ai-report.pdf"
    assert detail.official_summary == "공식 소개문입니다."


@pytest.mark.asyncio
async def test_rendered_adapter_list_detail(fixture_root: Path) -> None:
    config = load_source_config(fixture_root / "config/sample-rendered.yaml")
    pages = {
        str(config.list_url): (fixture_root / "html/sample-rendered-list.html").read_text(
            encoding="utf-8"
        ),
        "https://rendered.example/report/77": (
            fixture_root / "html/sample-rendered-detail.html"
        ).read_text(encoding="utf-8"),
    }
    adapter = RenderedBoardAdapter(config, FixtureBrowser(pages))
    items = await discovered(adapter)
    detail = await adapter.fetch_detail(items[0])
    assert detail.institution == "가상 렌더링 연구원"
    assert detail.attachments[0].file_name == "carbon.pdf"


@pytest.mark.asyncio
async def test_kihasa_rendered_list_uses_official_detail_link(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kihasa-research.yaml"))
    detail_url = "https://www.kihasa.re.kr/publish/report/view?type=research&seq=74916"
    pages = {
        str(config.list_url): (fixture_root / "html/kihasa-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kihasa-detail.html").read_text(encoding="utf-8"),
    }
    adapter = RenderedBoardAdapter(config, FixtureBrowser(pages))
    item = (await discovered(adapter))[0]
    detail = await adapter.fetch_detail(item)
    assert str(detail.detail_url) == detail_url
    assert detail.attachments == []


def test_date_parser_accepts_korean_date_format() -> None:
    assert _date("발간일 2026년 8월 21일") is not None


@pytest.mark.asyncio
async def test_detail_date_falls_back_to_verified_list_date(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kiep-research.yaml"))
    fallback_config = config.model_copy(
        update={"detail": config.detail.model_copy(update={"published_at": ".missing-date"})}
    )
    detail_url = "https://www.kiep.go.kr/gallery.es?mid=a10101020000&bid=0001&act=view&list_no=12535"
    pages = {
        str(fallback_config.list_url): (fixture_root / "html/kiep-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kiep-detail.html").read_text(encoding="utf-8"),
    }
    adapter = StaticBoardAdapter(fallback_config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail((await discovered(adapter))[0])
    assert detail.published_at.isoformat() == "2026-07-21"


@pytest.mark.asyncio
async def test_kei_rendered_fixture_reads_homepage_report(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kei-research.yaml"))
    detail_url = "https://www.kei.re.kr/elibList.es?mid=a10101000000&elibName=researchreport&act=view&c_id=770743&rn=1&nPage=1"
    pages = {
        str(config.list_url): (fixture_root / "html/kei-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kei-detail.html").read_text(encoding="utf-8"),
    }
    adapter = RenderedBoardAdapter(config, FixtureBrowser(pages))
    detail = await adapter.fetch_detail((await discovered(adapter))[0])
    assert detail.published_at.isoformat() == "2026-05-09"
    assert "홍수관리" in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_kiet_rendered_fixture_reads_public_summary(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kiet-research.yaml"))
    detail_url = "https://www.kiet.re.kr/research/reportView?report_no=1154&pg=1"
    pages = {
        str(config.list_url): (fixture_root / "html/kiet-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kiet-detail.html").read_text(encoding="utf-8"),
    }
    adapter = RenderedBoardAdapter(config, FixtureBrowser(pages))
    detail = await adapter.fetch_detail((await discovered(adapter))[0])
    assert detail.published_at.isoformat() == "2026-03-25"
    assert "산업정책" in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_keei_rendered_fixture_reads_public_summary(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/keei-research.yaml"))
    detail_url = "https://www.keei.re.kr/board.es?mid=a10101010000&bid=0001&act=view&list_no=127920"
    pages = {
        str(config.list_url): (fixture_root / "html/keei-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/keei-detail.html").read_text(encoding="utf-8"),
    }
    adapter = RenderedBoardAdapter(config, FixtureBrowser(pages))
    detail = await adapter.fetch_detail((await discovered(adapter))[0])
    assert detail.published_at.isoformat() == "2026-04-30"
    assert "공급망" in (detail.official_summary or "")


@pytest.mark.asyncio
async def test_kinu_static_fixture_reads_public_abstract(fixture_root: Path) -> None:
    config = load_source_config(Path("config/sources/kinu-research.yaml"))
    detail_url = "https://www.kinu.or.kr/main/module/report/view.do?idx=132801&nav_code=mai1674786094"
    pages = {
        str(config.list_url): (fixture_root / "html/kinu-list.html").read_text(encoding="utf-8"),
        detail_url: (fixture_root / "html/kinu-detail.html").read_text(encoding="utf-8"),
    }
    adapter = StaticBoardAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    detail = await adapter.fetch_detail((await discovered(adapter))[0])
    assert detail.published_at.isoformat() == "2026-03-31"
    assert "통일외교" in (detail.official_summary or "")
