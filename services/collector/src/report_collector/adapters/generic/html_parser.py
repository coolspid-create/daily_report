import re
from datetime import date
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl
from report_collector.domain.errors import SourceParseError
from report_collector.domain.models import Attachment, DiscoveredItem, SourceConfig, SourceDocument
from report_collector.services.source_filter_service import title_allowed


def _text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _date(value: str) -> date | None:
    match = re.search(
        r"(?P<year>\d{4})[./-]\s*(?P<month>\d{1,2})(?:[./-]|\s+)\s*(?P<day>\d{1,2})",
        value,
    )
    korean_match = re.search(r"(?P<year>\d{4})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일", value)
    selected = match or korean_match
    if not selected:
        return None
    try:
        return date(
            int(selected.group("year")),
            int(selected.group("month")),
            int(selected.group("day")),
        )
    except ValueError:
        return None


def _summary(node: Tag | None) -> str | None:
    value = _text(node)
    if not value:
        return None
    return value[:3000].rsplit(" ", 1)[0] if len(value) > 3000 else value


def parse_list(html: str, config: SourceConfig) -> list[DiscoveredItem]:
    selectors = config.selectors
    if not selectors:
        raise SourceParseError("HTML adapter requires selectors")
    soup = BeautifulSoup(html, "html.parser")
    items: list[DiscoveredItem] = []
    for node in soup.select(selectors.list_item):
        title_node = node.select_one(selectors.title)
        link_node = node.select_one(selectors.detail_link)
        href = link_node.get("href") if link_node else None
        if not title_node or not isinstance(href, str):
            continue
        detail_url = urljoin(str(config.list_url), href)
        key_attr = selectors.source_item_key_attr
        key = str(node.get(key_attr)) if key_attr and node.get(key_attr) else detail_url
        date_node = node.select_one(selectors.published_at) if selectors.published_at else None
        title = _text(title_node)
        if not title_allowed(title, config.filters):
            continue
        items.append(
            DiscoveredItem(
                source_item_key=key,
                title=title,
                detail_url=HttpUrl(detail_url),
                published_at=_date(_text(date_node)),
            )
        )
    if not items:
        raise SourceParseError(f"No items matched selector: {selectors.list_item}")
    return items


def parse_detail(html: str, item: DiscoveredItem, config: SourceConfig) -> SourceDocument:
    soup = BeautifulSoup(html, "html.parser")
    detail = config.detail
    institution = _text(soup.select_one(detail.institution)) if detail.institution else config.name
    detail_date = _date(_text(soup.select_one(detail.published_at))) if detail.published_at else None
    published = detail_date or item.published_at
    attachments: list[Attachment] = []
    for node in soup.select(detail.attachments) if detail.attachments else []:
        href = node.get("href")
        if not isinstance(href, str):
            continue
        url = urljoin(str(item.detail_url), href)
        name = _text(node) or PurePosixPath(urlparse(url).path).name
        extension = PurePosixPath(urlparse(url).path).suffix.lower().lstrip(".")
        if extension and extension not in config.filters.allowed_extensions:
            continue
        attachments.append(Attachment(url=HttpUrl(url), file_name=name))
    license_text = _text(soup.select_one(detail.license)) if detail.license else None
    official_summary = _summary(soup.select_one(detail.summary)) if detail.summary else None
    return SourceDocument(
        source_item_key=item.source_item_key,
        title=item.title,
        institution=institution or config.name,
        detail_url=item.detail_url,
        published_at=published,
        attachments=attachments,
        official_summary=official_summary,
        license_text=license_text,
        rights_status=config.rights_default,
    )
