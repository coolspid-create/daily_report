from pathlib import Path

import pytest
from report_collector.adapters.sources.kif.adapter import KifRenderedAdapter
from report_collector.adapters.sources.kisdi.adapter import KisdiAdapter
from report_collector.adapters.sources.kistep.adapter import KistepAdapter
from report_collector.adapters.sources.koti.adapter import KotiAdapter
from report_collector.adapters.sources.nabo.adapter import NaboAdapter
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


def fixture(fixture_root: Path, name: str) -> str:
    return (fixture_root / f"html/{name}.html").read_text(encoding="utf-8")


async def first(adapter):
    return await anext(adapter.discover(None))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("slug", "key", "detail_url", "summary", "has_file"),
    [
        (
            "kistep-research",
            "12001",
            "https://www.kistep.re.kr/reportAllDetail.es?mid=a10305010000&rpt_no=12001",
            "투자의 구조 변화",
            True,
        ),
        (
            "kistep-brief",
            "9911",
            "https://www.kistep.re.kr/board.es?mid=a10306010000&bid=0031&act=view&list_no=9911",
            "기술패권 정책",
            True,
        ),
    ],
)
async def test_kistep_boards(
    fixture_root: Path,
    slug: str,
    key: str,
    detail_url: str,
    summary: str,
    has_file: bool,
) -> None:
    config = load_source_config(Path(f"config/sources/{slug}.yaml"))
    pages = {
        str(config.list_url): fixture(fixture_root, f"{slug}-list"),
        detail_url: fixture(fixture_root, f"{slug}-detail"),
    }
    adapter = KistepAdapter(config, FixtureHttp(pages))  # type: ignore[arg-type]
    item = await first(adapter)
    detail = await adapter.fetch_detail(item)
    assert item.source_item_key == key
    assert summary in (detail.official_summary or "")
    assert bool(detail.attachments) is has_file


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("slug", "key", "summary"),
    [
        ("kisdi-policy", "50101", "산업과 이용자 정책"),
        ("kisdi-stat", "60101", "미디어 이용 행태"),
    ],
)
async def test_kisdi_boards(fixture_root: Path, slug: str, key: str, summary: str) -> None:
    config = load_source_config(Path(f"config/sources/{slug}.yaml"))
    list_html = fixture(fixture_root, f"{slug}-list")
    adapter_for_item = KisdiAdapter(
        config, FixtureHttp({str(config.list_url): list_html})  # type: ignore[arg-type]
    )
    item = await first(adapter_for_item)
    pages = {
        str(config.list_url): list_html,
        str(item.detail_url): fixture(fixture_root, f"{slug}-detail"),
    }
    detail = await KisdiAdapter(config, FixtureHttp(pages)).fetch_detail(item)  # type: ignore[arg-type]
    assert item.source_item_key == key
    assert summary in (detail.official_summary or "")
    assert "/report/fileDown.do?" in str(detail.attachments[0].url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("slug", "key", "summary"),
    [
        ("nabo-analysis", "8801", "재정사업의 집행 성과"),
        ("nabo-brief", "7701", "거시경제 지표"),
    ],
)
async def test_nabo_boards(fixture_root: Path, slug: str, key: str, summary: str) -> None:
    config = load_source_config(Path(f"config/sources/{slug}.yaml"))
    list_html = fixture(fixture_root, f"{slug}-list")
    item_adapter = NaboAdapter(config, FixtureHttp({str(config.list_url): list_html}))  # type: ignore[arg-type]
    item = await first(item_adapter)
    pages = {
        str(config.list_url): list_html,
        str(item.detail_url): fixture(fixture_root, f"{slug}-detail"),
    }
    detail = await NaboAdapter(config, FixtureHttp(pages)).fetch_detail(item)  # type: ignore[arg-type]
    assert item.source_item_key == key
    assert summary in (detail.official_summary or "")
    assert detail.attachments[0].declared_type == "application/pdf"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("slug", "key", "summary"),
    [
        ("koti-research", "4101", "국가 교통체계"),
        ("koti-brief", "4201", "도시 교통정책"),
    ],
)
async def test_koti_boards(fixture_root: Path, slug: str, key: str, summary: str) -> None:
    config = load_source_config(Path(f"config/sources/{slug}.yaml"))
    list_html = fixture(fixture_root, f"{slug}-list")
    item_adapter = KotiAdapter(config, FixtureHttp({str(config.list_url): list_html}))  # type: ignore[arg-type]
    item = await first(item_adapter)
    pages = {
        str(config.list_url): list_html,
        str(item.detail_url): fixture(fixture_root, f"{slug}-detail"),
    }
    detail = await KotiAdapter(config, FixtureHttp(pages)).fetch_detail(item)  # type: ignore[arg-type]
    assert item.source_item_key == key
    assert summary in (detail.official_summary or "")
    assert detail.attachments == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("slug", "key", "summary"),
    [
        ("kif-financial-brief", "3101", "금융시장의 주요 변화"),
        ("kif-research", "3201", "금융산업 구조 변화"),
    ],
)
async def test_kif_rendered_boards(
    fixture_root: Path, slug: str, key: str, summary: str
) -> None:
    config = load_source_config(Path(f"config/sources/{slug}.yaml"))
    list_html = fixture(fixture_root, f"{slug}-list")
    item_browser = FixtureBrowser({str(config.list_url): list_html})
    item = await first(KifRenderedAdapter(config, FixtureHttp({}), item_browser))  # type: ignore[arg-type]
    pages = {
        str(config.list_url): list_html,
        str(item.detail_url): fixture(fixture_root, f"{slug}-detail"),
    }
    detail = await KifRenderedAdapter(
        config, FixtureHttp({}), FixtureBrowser(pages)  # type: ignore[arg-type]
    ).fetch_detail(item)
    assert item.source_item_key == key
    assert summary in (detail.official_summary or "")
    assert detail.attachments == []
