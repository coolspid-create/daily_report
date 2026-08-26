import hashlib
import html as html_module
import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

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

COLLECTION_ITEM = re.compile(
    r'"date":"(?P<date>[^"]+)".{0,2500}?'
    r'"title":"(?P<title>[^"]+)".{0,1800}?'
    r'"url":"(?P<url>https://www\.pwc\.com/kr/ko/[^"]+)"',
    re.DOTALL,
)


class SamilPwcAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, browser: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http
        self.browser = browser

    async def _html(self, url: str, wait_for: str | None = None) -> str:
        if self.browser:
            return await self.browser.render(url, wait_for, self.config.browser.timeout_ms)
        return await self.http.fetch_text(url)

    def _parse_list(self, raw_html: str) -> list[DiscoveredItem]:
        decoded = html_module.unescape(raw_html)
        found: dict[str, DiscoveredItem] = {}
        for match in COLLECTION_ITEM.finditer(decoded):
            title = html_module.unescape(match.group("title")).replace(" | 삼일PwC", "").strip()
            url = match.group("url").replace("\\/", "/")
            if not title or "/insights/" not in url:
                continue
            published_at = _english_date(match.group("date"))
            key = hashlib.sha256(url.encode()).hexdigest()[:24]
            found.setdefault(
                key,
                DiscoveredItem(
                    source_item_key=key,
                    title=title,
                    detail_url=HttpUrl(url),
                    published_at=published_at,
                ),
            )
        if not found:
            soup = BeautifulSoup(raw_html, "html.parser")
            for anchor in soup.select(".collection__item a[href]"):
                url = urljoin(str(self.config.list_url), str(anchor.get("href", "")))
                if "/kr/ko/" not in url or "/insights/" not in url:
                    continue
                parts = [part.strip() for part in anchor.get_text("\n", strip=True).splitlines() if part.strip()]
                if len(parts) < 2:
                    continue
                title = parts[1]
                key = hashlib.sha256(url.encode()).hexdigest()[:24]
                found.setdefault(
                    key,
                    DiscoveredItem(
                        source_item_key=key,
                        title=title,
                        detail_url=HttpUrl(url),
                        published_at=_month_date(parts[0]),
                    ),
                )
            for anchor in soup.select("a[href*='/press-room/2026/']"):
                url = urljoin(str(self.config.list_url), str(anchor.get("href", "")))
                context = (anchor.find_parent(["article", "li", "div"]) or anchor).get_text(
                    " ", strip=True
                )
                if not any(keyword in context for keyword in ("보고서", "발간", "분석")):
                    continue
                title = anchor.get_text(" ", strip=True)
                published_at = _date_from_press_url(url)
                if len(title) < 5 or not published_at:
                    continue
                key = hashlib.sha256(url.encode()).hexdigest()[:24]
                found.setdefault(
                    key,
                    DiscoveredItem(
                        source_item_key=key,
                        title=title,
                        detail_url=HttpUrl(url),
                        published_at=published_at,
                    ),
                )
        if not found:
            raise SourceParseError("Samil PwC collection items not found")
        return list(found.values())

    async def _items(self) -> list[DiscoveredItem]:
        found: dict[str, DiscoveredItem] = {}
        for url in self.config.collection_urls or [self.config.list_url]:
            try:
                page_items = self._parse_list(
                    await self._html(str(url), ".collection__item, a[href*='/press-room/2026/']")
                )
            except SourceParseError:
                continue
            for item in page_items:
                found.setdefault(item.source_item_key, item)
        if not found:
            raise SourceParseError("Samil PwC collection items not found")
        return sorted(found.values(), key=lambda item: item.published_at or date.min, reverse=True)

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in await self._items():
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        url = str(item.detail_url)
        if url.lower().endswith(".pdf"):
            return SourceDocument(
                source_item_key=item.source_item_key,
                title=item.title,
                institution=self.config.name,
                detail_url=item.detail_url,
                published_at=item.published_at,
                attachments=[
                    Attachment(
                        url=item.detail_url, file_name=PurePosixPath(urlparse(url).path).name
                    )
                ],
                official_summary=item.title,
                rights_status=self.config.rights_default,
            )
        soup = BeautifulSoup(await self._html(url), "html.parser")
        published_at = item.published_at
        for selector in (
            "meta[property='article:published_time']",
            "meta[name='publication-date']",
            "meta[name='date']",
        ):
            node = soup.select_one(selector)
            if node and node.get("content"):
                published_at = _iso_date(str(node["content"])) or published_at
                if published_at:
                    break
        summary = " ".join(
            p.get_text(" ", strip=True)
            for p in soup.select("main p, article p")
            if len(p.get_text(" ", strip=True)) > 30
        )[:3000]
        attachments: list[Attachment] = []
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"])
            full_url = urljoin(url, href).split("#")[0]
            path = urlparse(full_url).path.lower()
            if not path.endswith(".pdf") or "/content/dam/pwc/kr/" not in path or full_url in seen:
                continue
            seen.add(full_url)
            attachments.append(
                Attachment(
                    url=HttpUrl(full_url),
                    file_name=PurePosixPath(urlparse(full_url).path).name,
                    declared_type="application/pdf",
                )
            )
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=published_at,
            attachments=attachments,
            official_summary=summary or item.title,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(await self._items())
            return SourceHealthResult(
                healthy=True,
                checked_at=datetime.now(UTC),
                message=f"{count} official PwC insights parsed",
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _english_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%a %b %d %H:%M:%S UTC %Y").date()
    except ValueError:
        return None


def _month_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%B %Y").date()
    except ValueError:
        return None


def _iso_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _date_from_press_url(value: str) -> date | None:
    match = re.search(r"/20\d{2}/(?P<stamp>20\d{6})\.html", value)
    if not match:
        return None
    try:
        return datetime.strptime(match.group("stamp"), "%Y%m%d").date()
    except ValueError:
        return None
