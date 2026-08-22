import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
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

VIEW_PATTERN = re.compile(r"goView\(['\"](?P<master>\d+)['\"],\s*['\"](?P<id>\d+)['\"]\)")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class KisdiAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[DiscoveredItem] = []
        for node in soup.select("#dataList > li.renew"):
            link = node.select_one("a[onclick*='goView']")
            match = VIEW_PATTERN.search(str(link.get("onclick", ""))) if link else None
            title_node = link.select_one(":scope > strong") if link else None
            if not match or not title_node:
                continue
            title = title_node.get_text(" ", strip=True)
            if not title_allowed(title, self.config.filters):
                continue
            detail = _detail_url(str(self.config.list_url), match.group("master"), match.group("id"))
            results.append(
                DiscoveredItem(
                    source_item_key=match.group("id"),
                    title=title,
                    detail_url=HttpUrl(detail),
                    published_at=_date(node.get_text(" ", strip=True)),
                )
            )
        if not results:
            raise SourceParseError("KISDI report list structure changed")
        return results

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        attachment = _download_attachment(str(item.detail_url), item.source_item_key)
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=_date(soup.get_text(" ", strip=True)) or item.published_at,
            attachments=[attachment],
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


def _detail_url(list_url: str, master: str, item_id: str) -> str:
    query = parse_qs(urlparse(list_url).query)
    key = query.get("key", [""])[0]
    arr_master = query.get("arrMasterId", [master])[0]
    return urljoin(
        list_url,
        f"/report/view.do?key={key}&masterId={master}&arrMasterId={arr_master}&artId={item_id}",
    )


def _download_attachment(detail_url: str, item_id: str) -> Attachment:
    query = parse_qs(urlparse(detail_url).query)
    key = query.get("key", [""])[0]
    master = query.get("arrMasterId", query.get("masterId", [""]))[0]
    url = urljoin(detail_url, f"/report/fileDown.do?key={key}&arrMasterId={master}&id={item_id}")
    return Attachment(
        url=HttpUrl(url),
        file_name=f"kisdi-{item_id}.pdf",
        declared_type="application/pdf",
    )


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group()) if match else None


def _summary(soup: BeautifulSoup) -> str | None:
    node = soup.select_one(".view_cont, .board_view, #contents")
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip() if node else ""
    return text[:3000] or None
