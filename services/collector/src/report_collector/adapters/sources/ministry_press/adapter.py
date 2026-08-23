import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urljoin, urlparse

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

DATE_PATTERN = re.compile(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})")
DOC_ID_PATTERN = re.compile(r"(?:fn_selectDoc|goView|fn_view|selectDoc|viewDoc)\(['\"]?(\d+)['\"]?\)")
NOISE_KEYWORDS = ("동정", "포토", "행사", "채용", "입찰", "공고", "인사", "일정")


class MinistryPressAdapter(SourceAdapter):
    """대한민국 중앙행정기관(정부 부처) 표준 보도자료 게시판을 수집합니다."""

    def __init__(
        self,
        config: SourceConfig,
        http: PublicHttpClient,
        _: BrowserRenderer | None = None,
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        row_selector = (
            self.config.selectors.list_item
            if self.config.selectors and self.config.selectors.list_item
            else "tbody tr"
        )
        nodes = soup.select(row_selector)
        if not nodes:
            # Fallback to general list items
            nodes = soup.select("ul.board-list li, .board-list-wrap li, .list-body > div")


        items: list[DiscoveredItem] = []
        for node in nodes:
            item = _parse_row(node, self.config)
            if item and title_allowed(item.title, self.config.filters):
                items.append(item)


        if not items and not nodes:
            raise SourceParseError(f"{self.config.name} publication list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self.http.fetch_text(str(self.config.list_url))
        for item in self._parse_list(html):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")
        content_text = soup.get_text(" ", strip=True)
        published_at = _extract_date(content_text) or item.published_at

        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=published_at,
            attachments=_extract_attachments(soup, str(item.detail_url)),
            official_summary=_extract_summary(soup),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self.http.fetch_text(str(self.config.list_url))
            parsed = self._parse_list(html)
            return SourceHealthResult(
                healthy=True,
                checked_at=datetime.now(UTC),
                message=f"{len(parsed)} press releases parsed",
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False,
                checked_at=datetime.now(UTC),
                message=str(error),
            )


def _parse_row(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one(
        "td.tit a, td.title a, td.subject a, .subject a, .tit a, a[href*='selectDoc'], a[href*='view']"
    ) or node.find("a")
    if not isinstance(link, Tag):
        return None

    title = link.get_text(" ", strip=True)
    if not title:
        title = str(link.get("title", "")).strip()
    if not title or len(title) < 2:
        return None

    href = str(link.get("href", "")).strip()
    onclick = str(link.get("onclick", "")).strip()
    detail_url = _build_url(href, onclick, config)
    if not detail_url:
        return None

    row_text = node.get_text(" ", strip=True)
    published_date = _extract_date(row_text) or date.today()
    item_key = _make_item_key(detail_url, onclick, title)

    return DiscoveredItem(
        source_item_key=item_key,
        title=title,
        detail_url=HttpUrl(detail_url),
        published_at=published_date,
    )


def _build_url(href: str, onclick: str, config: SourceConfig) -> str | None:
    if href and href != "#" and not href.startswith("javascript:"):
        return urljoin(str(config.list_url), href)

    match = DOC_ID_PATTERN.search(onclick) or DOC_ID_PATTERN.search(href)
    if match:
        doc_id = match.group(1)
        base = str(config.list_url)
        if "selectDocList" in base:
            return base.replace("selectDocList.do", "selectDoc.do") + f"&docSeq={doc_id}"
        if "boardList" in base:
            return base.replace("boardList.do", "boardView.do") + f"&nttId={doc_id}"
        return f"{base}?docSeq={doc_id}"

    if href and href != "#":
        return urljoin(str(config.list_url), href)
    return None


def _make_item_key(url: str, onclick: str, title: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    for key in ("docSeq", "nttId", "seq", "bbsId", "articleId", "artclRowId"):
        if key in qs and qs[key]:
            return f"{key}-{qs[key][0]}"

    match = DOC_ID_PATTERN.search(onclick)
    if match:
        return f"doc-{match.group(1)}"

    # Path-based key or hash of title
    path_clean = parsed.path.strip("/").replace("/", "-")
    return f"{path_clean}-{abs(hash(title)) % 1000000}"


def _extract_date(text: str) -> date | None:
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _extract_attachments(soup: Tag, base_url: str) -> list[Attachment]:
    attachments: list[Attachment] = []
    for a in soup.select("a[href*='download'], a[href*='fileDown'], a[href*='FileDown'], .file a, .attach a"):
        href = str(a.get("href", "")).strip()
        if not href or href.startswith("javascript:void"):
            continue
        name = a.get_text(strip=True) or "첨부파일"
        ext = "PDF" if ".pdf" in name.lower() or "pdf" in href.lower() else "HWP"
        full_url = urljoin(base_url, href)
        attachments.append(Attachment(file_name=name, url=HttpUrl(full_url), declared_type=ext))
    return attachments



def _extract_summary(soup: Tag) -> str | None:
    content_node = soup.select_one(".view-content, .board-view-content, .bbs_view, .board_view, .content-area, article")
    if not content_node:
        return None
    text = content_node.get_text(" ", strip=True)
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:300] if clean else None
