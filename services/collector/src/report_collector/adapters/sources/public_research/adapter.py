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
from soupsieve import match

DATE_PATTERN = re.compile(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}")


class PublicResearchAdapter(SourceAdapter):
    """Reads only public HTML report boards and their official detail/file links."""

    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config, self.http = config, http

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        return SourceDocument(
            source_item_key=item.source_item_key, title=item.title, institution=self.config.name,
            detail_url=item.detail_url, published_at=_date(_text(soup, self.config.detail.published_at)) or item.published_at,
            attachments=_attachments(soup, str(item.detail_url), self.config.detail.attachments),
            official_summary=_summary(soup, self.config.detail.summary), rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        if not self.config.selectors:
            raise SourceParseError("Public research adapter requires selectors")
        soup = BeautifulSoup(html, "html.parser")
        items = [item for node in soup.select(self.config.selectors.list_item) if (item := _item(node, self.config))]
        if not items:
            raise SourceParseError(f"{self.config.id} report list structure changed")
        return items


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    assert config.selectors
    title_node = _select(node, config.selectors.title)
    link = _select(node, config.selectors.detail_link)
    title = _node_text(title_node)
    raw_link = _link_value(link) if link else ""
    key = _key(raw_link, config.source_item_key_pattern)
    if not key or not title or not title_allowed(title, config.filters):
        return None
    url = config.detail_url_template.format(key=key) if config.detail_url_template else urljoin(str(config.list_url), raw_link)
    return DiscoveredItem(source_item_key=key, title=title, detail_url=HttpUrl(url), published_at=_date(node.get_text(" ", strip=True)))


def _key(value: str, pattern: str | None) -> str | None:
    if pattern:
        match = re.search(pattern, value)
        return match.group(1) if match else None
    match = re.search(r"(?:[?&](?:idx|num|id)=|/view/)([A-Za-z0-9_-]+)", value)
    return match.group(1) if match else None


def _link_value(link: Tag) -> str:
    href = str(link.get("href", ""))
    onclick = str(link.get("onclick", ""))
    return href if href and not href.lower().startswith("javascript:") else onclick or href


def _select(node: Tag, selector: str) -> Tag | None:
    """Return a matching node itself before looking for a matching child."""
    return node if match(selector, node) else node.select_one(selector)


def _attachments(soup: BeautifulSoup, base: str, selector: str | None) -> list[Attachment]:
    if not selector:
        return []
    attachments: list[Attachment] = []
    for link in soup.select(selector):
        href = _attachment_url(link, base)
        if not href:
            continue
        attachments.append(
            Attachment(url=HttpUrl(href), file_name="official-report.pdf", declared_type="application/pdf")
        )
    return attachments


def _attachment_url(link: Tag, base: str) -> str | None:
    href = str(link.get("href", ""))
    if href and not href.lower().startswith("javascript:"):
        return urljoin(base, href)
    onclick = str(link.get("onclick", ""))
    match = re.search(r"fileDown\(['\"]?([^,'\")]+)['\"]?\s*,\s*['\"]?([^,'\")]+)", onclick)
    if not match:
        return None
    return urljoin(base, f"/file/fileDown.do?file_seq={match.group(1)}&file_sn={match.group(2)}")


def _summary(soup: BeautifulSoup, selector: str | None) -> str | None:
    text = _text(soup, selector)
    return re.sub(r"\s+", " ", text).strip()[:3000] or None


def _text(soup: BeautifulSoup, selector: str | None) -> str:
    return _node_text(soup.select_one(selector)) if selector else ""


def _node_text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    if not match:
        return None
    parts = re.split(r"[./-]", match.group())
    return date(int(parts[0]), int(parts[1]), int(parts[2]))
