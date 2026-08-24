import hashlib
import logging
import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
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
from report_collector.services.source_filter_service import title_allowed

DATE_PATTERN = re.compile(r"(?P<year>20\d{2})\s*[./년-]\s*(?P<month>\d{1,2})(?:\s*[./월-]\s*(?P<day>\d{1,2}))?")
logger = logging.getLogger(__name__)

EXCLUDED_PATHS = {
    "/kr/ko/our-thinking/deloitte-insights.html",
    "/kr/ko/our-thinking/deloitte-insights-publications.html",
    "/kr/ko/our-thinking/deloitte-global-economic-review.html",
    "/kr/ko/our-thinking/mobile-app-kakao.html",
    "/kr/ko/issues/climate/sustainability-and-climate.html",
    "/kr/ko/issues/generative-ai.html",
    "/kr/ko/our-thinking/deloitte-at-ces.html",
    "/kr/ko/our-thinking/insights-archive.html",
    "/kr/ko/Industries/consumer/research/consumer-signal-index.html",
}

EXCLUDED_SEGMENTS = {
    "privacy", "legal", "about", "contact", "careers", "sitemap",
    "events", "profiles", "case-studies", "alumni", "offices",
    "what-we-do", "search", "terms", "nonprofit", "join."
}


class DeloitteInsightsAdapter(SourceAdapter):
    """딜로이트 코리아(Deloitte Korea) 인사이트 및 리서치 발간 보고서를 수집합니다."""

    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        main_node = soup.select_one("main, #main, .root, .responsivegrid") or soup
        found: dict[str, DiscoveredItem] = {}

        for a in main_node.find_all("a", href=True):
            href = str(a["href"]).strip()
            heading = a.select_one("h1, h2, h3, h4, .title, strong, [class*='title']")
            title = heading.get_text(" ", strip=True) if heading else a.get_text(" ", strip=True)
            title = re.sub(r"\s+", " ", title).strip()

            if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            if len(title) < 4 or not title_allowed(title, self.config.filters):
                continue

            parsed = urlparse(href)
            path_clean = parsed.path
            path_lower = path_clean.lower()

            if path_clean in EXCLUDED_PATHS or any(seg in path_lower for seg in EXCLUDED_SEGMENTS):
                continue

            is_report_path = any(
                k in path_lower
                for k in [
                    "perspectives",
                    "monthly-trend-tracker",
                    "predictions",
                    "trend",
                    "survey",
                    "ai-use-cases",
                    "/research/",
                ]
            )
            if not is_report_path:
                continue

            full_url = urljoin(str(self.config.list_url), href)
            clean_url = full_url.split("?")[0]
            key = _extract_key(clean_url, title)

            parent = a.find_parent(["div", "li", "article", "section"]) or a
            parent_text = parent.get_text(" ", strip=True)
            pub_date = _extract_date(parent_text) or _extract_date_from_url(clean_url)

            if key not in found:
                found[key] = DiscoveredItem(
                    source_item_key=key,
                    title=title,
                    detail_url=HttpUrl(clean_url),
                    published_at=pub_date,
                )

        if not found:
            raise SourceParseError("Deloitte Insights publication items not found")
        return list(found.values())

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self.http.fetch_text(str(self.config.list_url))
        for item in self._parse_list(html):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.select("header, nav, footer, .global-header, .global-footer, .header, .footer"):
            tag.decompose()

        article_node = soup.select_one("article, main, .article, .root, .cmp-text")
        summary_text = ""
        if article_node:
            paragraphs = [
                p.get_text(" ", strip=True)
                for p in article_node.find_all(["p", "h2", "h3"])
                if len(p.get_text(strip=True)) > 20 and not p.get_text(strip=True).startswith("Together makes")
            ]
            summary_text = " ".join(paragraphs)[:3000]

        pub_date = item.published_at
        if not pub_date:
            meta_date = soup.select_one("meta[name='publication-date'], meta[property='article:published_time']")
            if meta_date and meta_date.get("content"):
                pub_date = _extract_date(str(meta_date["content"]))
            if not pub_date and article_node:
                pub_date = _extract_date(article_node.get_text(" ", strip=True))

        attachments = _extract_attachments(soup, str(item.detail_url))

        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=pub_date,
            attachments=attachments,
            official_summary=summary_text or item.title,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self.http.fetch_text(str(self.config.list_url))
            items = self._parse_list(html)
            return SourceHealthResult(
                healthy=True,
                checked_at=datetime.now(UTC),
                message=f"{len(items)} Deloitte publications parsed",
            )
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _extract_key(url: str, title: str) -> str:
    path = urlparse(url).path.strip("/").replace(".html", "")
    parts = [p for p in path.split("/") if p]
    if parts:
        slug = "-".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
        return slug[:64]
    return hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]


def _extract_date(text: str) -> date | None:
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day")) if match.group("day") else 1
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _extract_date_from_url(url: str) -> date | None:
    match = re.search(r"(?P<year>20\d{2})[-_/](?P<month>\d{1,2})", url)
    if match:
        try:
            return date(int(match.group("year")), int(match.group("month")), 1)
        except ValueError:
            return None
    year_match = re.search(r"(?P<year>20\d{2})", url)
    if year_match:
        try:
            return date(int(year_match.group("year")), 1, 1)
        except ValueError:
            return None
    return None


def _extract_attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    attachments: list[Attachment] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        if not href or href.startswith("javascript:"):
            continue
        if ".pdf" in href.lower() or "/content/dam/" in href:
            full_url = urljoin(base_url, href).split("#")[0]
            if full_url not in seen:
                seen.add(full_url)
                name = a.get_text(" ", strip=True) or a.get("title") or "Deloitte-Report.pdf"
                clean_name = str(name).strip()
                if not clean_name.lower().endswith(".pdf"):
                    clean_name = f"{clean_name}.pdf"
                attachments.append(
                    Attachment(
                        url=HttpUrl(full_url),
                        file_name=clean_name,
                        declared_type="application/pdf",
                    )
                )

    return attachments
