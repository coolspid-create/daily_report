import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl
from report_collector.adapters.base import SourceAdapter
from report_collector.domain.errors import SourceParseError
from report_collector.domain.models import (
    Attachment,
    DiscoveredItem,
    SourceConfig,
    SourceDocument,
    SourceHealthResult,
)
from report_collector.providers.browser.base import BrowserRenderer
from report_collector.providers.http.http_client import PublicHttpClient
from report_collector.services.source_filter_service import title_allowed

VIEW_PATTERN = re.compile(r"setView\(['\"](?P<id>\d+)['\"],['\"]ib['\"]\)")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class InssAdapter(SourceAdapter):
    """읽기 가능한 공개 목록과 상세 HTML만 사용하는 이슈브리프 수집기."""

    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[DiscoveredItem] = []
        for node in soup.select("ul.listType01 > li"):
            link = node.select_one(".txtBox a[onclick*='setView']")
            match = VIEW_PATTERN.search(str(link.get("onclick", ""))) if link else None
            if not link or not match:
                continue
            title = link.get_text(" ", strip=True)
            if not title_allowed(title, self.config.filters):
                continue
            date_match = DATE_PATTERN.search(node.get_text(" ", strip=True))
            published = date.fromisoformat(date_match.group()) if date_match else None
            item_id = match.group("id")
            items.append(
                DiscoveredItem(
                    source_item_key=item_id,
                    title=title,
                    detail_url=HttpUrl(
                        f"https://www.inss.re.kr/publication/bbs/ib_view.do?bbsId=ib&nttId={item_id}"
                    ),
                    published_at=published,
                )
            )
        if not items:
            raise SourceParseError("INSS issue brief list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=_detail_date(soup) or item.published_at,
            attachments=_attachments(soup, str(item.detail_url)),
            official_summary=_summary(soup),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _detail_date(soup: BeautifulSoup) -> date | None:
    label = soup.find("dt", string=lambda value: value and "발행일" in value)
    value = label.find_next_sibling("dd") if isinstance(label, Tag) else None
    match = DATE_PATTERN.search(value.get_text(" ", strip=True)) if value else None
    return date.fromisoformat(match.group()) if match else None


def _attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    links = soup.select("a[href*='/common/download.do?']")
    return [
        Attachment(
            url=HttpUrl(urljoin(base_url, str(link.get("href")))),
            file_name="국가안보전략연구원_이슈브리프.pdf",
            declared_type="application/pdf",
        )
        for link in links
    ]


def _summary(soup: BeautifulSoup) -> str | None:
    content = soup.select_one("#view_content")
    if content is None:
        return None
    text = re.sub(r"\s+", " ", content.get_text(" ", strip=True)).strip()
    return text or None
