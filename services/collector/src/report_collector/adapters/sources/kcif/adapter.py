import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import urljoin

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

_PATH = re.compile(r"/(?:annual|finance|economy)/(?:reportView|financeView|economyView)\?rpt_no=(\d+)")
_DATE = re.compile(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})")


class KcifPublicReportAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config, self.http = config, http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        found: dict[str, DiscoveredItem] = {}
        for link in soup.select("a[href]"):
            href = str(link["href"])
            match = _PATH.search(href)
            title = link.get_text(" ", strip=True)
            if not match or not title_allowed(title, self.config.filters):
                continue
            node = link.find_parent(["li", "tr"]) or link.find_parent("div") or link
            found.setdefault(
                match.group(1),
                DiscoveredItem(
                    source_item_key=match.group(1),
                    title=title,
                    detail_url=HttpUrl(urljoin(str(self.config.homepage_url), href)),
                    published_at=_date(node.get_text(" ", strip=True)),
                ),
            )
        if not found:
            raise SourceParseError("KCIF public report links not found")
        return list(found.values())

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")
        content = next(
            (
                soup.select_one(selector)
                for selector in (".cont_area", ".con_wrap", ".board_view", ".view_cont", "article")
                if soup.select_one(selector)
            ),
            None,
        )
        text = re.sub(r"\s+", " ", content.get_text(" ", strip=True)).strip() if content else ""
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=item.published_at,
            attachments=_attachments(soup, str(item.detail_url)),
            official_summary=text[:3000] or None,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            return SourceHealthResult(
                healthy=True,
                checked_at=datetime.now(UTC),
                message=f"{len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))} items parsed",
            )
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _date(text: str) -> date | None:
    match = _DATE.search(text)
    return date(*map(int, match.groups())) if match else None


def _attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    attachments: list[Attachment] = []
    seen_urls: set[str] = set()

    for link in soup.select("a[href]"):
        href = str(link["href"]).strip()
        if ".pdf" in href.lower() and not href.startswith("javascript:"):
            full_url = urljoin(base_url, href)
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                attachments.append(
                    Attachment(
                        url=HttpUrl(full_url),
                        file_name=link.get_text(" ", strip=True) or "KCIF-report.pdf",
                        declared_type="application/pdf",
                    )
                )

    for el in soup.select("[onclick*='reportdownload'], [onclick*='engReportdownload']"):
        onclick = str(el.get("onclick", ""))
        match = re.search(r"reportdownload\(['\"]([^'\"]+)['\"]\)", onclick)
        if match:
            fno = match.group(1)
            download_url = f"https://www.kcif.or.kr/common/file/reportFileDownload?atch_no={fno}&lang=KR"
            if download_url not in seen_urls:
                seen_urls.add(download_url)
                raw_name = el.get_text(" ", strip=True) or el.get("title") or el.get("kcif-title") or "KCIF-report"
                clean_name = str(raw_name).strip()
                if not clean_name.lower().endswith(".pdf"):
                    clean_name = f"{clean_name}.pdf"
                attachments.append(
                    Attachment(
                        url=HttpUrl(download_url),
                        file_name=clean_name,
                        declared_type="application/pdf",
                    )
                )

    return attachments
