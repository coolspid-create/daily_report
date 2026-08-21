import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import quote

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

VIEW_PATTERN = re.compile(r"view\(['\"](\d+)['\"]\)")
FILE_PATTERN = re.compile(
    r"openPdfViewer\('\S*?doc_id=([^&']+).*?','([^']+?\.pdf)'\)", re.DOTALL
)
DOWNLOAD_PATTERN = re.compile(r"fileDownLoad\('\s*([^',]+)\s*'\s*,\s*'([^']+?\.pdf)'\)")
DATE_PATTERN = re.compile(r"\d{4}\.\d{2}\.\d{2}")


class NarsAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[DiscoveredItem] = []
        for node in soup.select("ul.brdl-tp1 > li"):
            link = node.select_one("div.tt a")
            match = VIEW_PATTERN.search(str(link.get("href", ""))) if link else None
            if not link or not match:
                continue
            title = link.get_text(" ", strip=True)
            if not title_allowed(title, self.config.filters):
                continue
            item_id = match.group(1)
            date_match = DATE_PATTERN.search(node.get_text(" ", strip=True))
            published = (
                date.fromisoformat(date_match.group().replace(".", "-")) if date_match else None
            )
            url = f"https://www.nars.go.kr/report/view.do?brdSeq={item_id}&cmsCode=CM0043"
            results.append(
                DiscoveredItem(
                    source_item_key=item_id,
                    title=title,
                    detail_url=HttpUrl(url),
                    published_at=published,
                )
            )
        if not results:
            raise SourceParseError("NARS report list structure changed")
        return results

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")
        attachments = _attachments(html)
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=item.published_at,
            attachments=attachments,
            official_summary=_official_summary(soup),
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


def _official_summary(soup: BeautifulSoup) -> str | None:
    content = soup.select_one("div.vw-con")
    if content is None:
        return None
    summary = re.sub(r"\s+", " ", content.get_text(" ", strip=True)).strip()
    return summary or None


def _attachments(html: str) -> list[Attachment]:
    matches = [*FILE_PATTERN.finditer(html), *DOWNLOAD_PATTERN.finditer(html)]
    return [
        Attachment(
            url=HttpUrl(
                "https://www.nars.go.kr/fileDownload2.do"
                f"?doc_id={match.group(1)}&fileName={quote(match.group(2))}"
            ),
            file_name=match.group(2),
            declared_type="application/pdf",
        )
        for match in matches
    ]
