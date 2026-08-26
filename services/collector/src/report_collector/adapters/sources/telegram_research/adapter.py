import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import PurePosixPath
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

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


class OfficialTelegramResearchAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http
        self.resolved: dict[str, str] = {}
        self.report_urls: dict[str, str] = {}
        self.summaries: dict[str, str] = {}

    def _parse_messages(self, html: str) -> list[tuple[DiscoveredItem, str]]:
        soup = BeautifulSoup(html, "html.parser")
        parsed: list[tuple[DiscoveredItem, str]] = []
        for message in soup.select(".tgme_widget_message[data-post]"):
            text_node = message.select_one(".tgme_widget_message_text")
            time_node = message.select_one("time[datetime]")
            if not text_node or not time_node:
                continue
            links = [str(a.get("href")) for a in text_node.find_all("a", href=True)]
            report_url = self._select_report_link(links)
            if not report_url:
                continue
            raw_text = _message_text(text_node)
            post_path = str(message.get("data-post", "")).strip("/")
            post_key = post_path.replace("/", "-")
            title = _extract_title(raw_text)
            if not post_path or not title:
                continue
            self.report_urls[post_key] = report_url.replace("http://", "https://")
            self.summaries[post_key] = raw_text[:3000]
            published_at = (
                datetime.fromisoformat(str(time_node["datetime"]).replace("Z", "+00:00"))
                .astimezone(ZoneInfo("Asia/Seoul"))
                .date()
            )
            parsed.append(
                (
                    DiscoveredItem(
                        source_item_key=post_key,
                        title=title,
                        detail_url=HttpUrl(f"https://t.me/{post_path}"),
                        published_at=published_at,
                    ),
                    raw_text[:3000],
                )
            )
        return sorted(
            parsed,
            key=lambda value: int(value[0].source_item_key.rsplit("-", 1)[-1]),
            reverse=True,
        )

    def _select_report_link(self, links: list[str]) -> str | None:
        if self.config.id == "kiwoom-research":
            return next((url for url in links if "bbn.kiwoom.com/" in url), None)
        return next((url for url in links if "buly.kr/" in url), None)

    async def _items(self, resolve: bool) -> list[DiscoveredItem]:
        messages = self._parse_messages(await self.http.fetch_text(str(self.config.list_url)))
        items: list[DiscoveredItem] = []
        for item, _ in messages:
            if resolve and self.config.id == "sk-securities-research":
                result = await self.http.fetch(
                    self.report_urls[item.source_item_key], max_bytes=25_000_000
                )
                final_url = result.final_url.replace("http://", "https://")
                parsed = urlparse(final_url)
                if (
                    not parsed.hostname
                    or not parsed.hostname.endswith("sks.co.kr")
                    or "/data1/research/" not in parsed.path
                ):
                    continue
                self.resolved[item.source_item_key] = final_url
            items.append(item)
        if not items:
            raise SourceParseError(f"No official report links found for {self.config.id}")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in await self._items(resolve=True):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        final_url = self.resolved.get(
            item.source_item_key, self.report_urls[item.source_item_key]
        ).replace("http://", "https://")
        parsed = urlparse(final_url)
        name = PurePosixPath(parsed.path).name or f"{item.source_item_key}.pdf"
        if not name.lower().endswith(".pdf"):
            name = f"{name}.pdf"
        official_file_url = HttpUrl(final_url)
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=item.published_at,
            attachments=[
                Attachment(
                    url=official_file_url, file_name=name, declared_type="application/pdf"
                )
            ],
            official_summary=self.summaries.get(item.source_item_key, item.title),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(await self._items(resolve=False))
            return SourceHealthResult(
                healthy=True,
                checked_at=datetime.now(UTC),
                message=f"{count} official channel report links parsed",
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


_BOILERPLATE = (
    "이번 자료는",
    "많은 관심 부탁",
    "아래 내용은",
)
_LABEL_PATTERN = re.compile(r"^(?:▶️?|♣️?|🔗|🎯|📌|보고서(?: 원문)?|자료링크|URL)\s*:?$", re.I)
_DETAIL_PATTERN = re.compile(r"^(?:\d+[.)]|[①-⑳]|[-•])\s*")


def _extract_title(raw_text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line and not _ignored_title_line(line)]
    if not lines:
        return ""

    analyst_indexes = [
        index
        for index, line in enumerate(lines)
        if line.startswith("[")
        and line.endswith("]")
        and ("키움" in line or "SK증권" in line)
    ]
    first = lines[0]

    if first.startswith("[") and "]" in first and "Analyst" in first:
        header = first.split("]", 1)[0] + "]"
        candidate = _first_title_candidate(lines[1:])
        if candidate:
            return _limit_title(f"{header} {candidate}")

    if any(marker in first for marker in _BOILERPLATE) and analyst_indexes:
        analyst_index = analyst_indexes[-1]
        candidate = _first_title_candidate(lines[analyst_index + 1 :])
        if candidate:
            return _limit_title(f"{lines[analyst_index]} {candidate}")

    if analyst_indexes and analyst_indexes[0] == 0:
        candidate = _first_title_candidate(lines[1:])
        if candidate:
            return _limit_title(f"{first} {candidate}")

    if len(lines) > 1 and lines[1].startswith("- ") and not first.startswith("["):
        return _limit_title(f"{first} {lines[1]}")
    return _limit_title(first)


def _first_title_candidate(lines: list[str]) -> str | None:
    for line in lines:
        if _DETAIL_PATTERN.match(line) or any(marker in line for marker in _BOILERPLATE):
            continue
        return re.sub(r"^[▶♣🔗🎯📌]️?\s*", "", line).removesuffix("(요약)").strip()
    return None


def _ignored_title_line(line: str) -> bool:
    lowered = line.lower()
    return bool(
        _LABEL_PATTERN.match(line)
        or lowered.startswith(("http://", "https://", "www."))
        or bool(re.fullmatch(r"[()[\]{}]+", line))
        or "@" in line
        or "카카오톡 채널" in line
        or "compliance notice" in lowered
    )


def _limit_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    if len(title) > 120 and " - " in title:
        title = title.split(" - ", 1)[0].rstrip()
    return title if len(title) <= 120 else title[:117].rstrip() + "..."


def _message_text(text_node: Tag) -> str:
    node = BeautifulSoup(str(text_node), "html.parser")
    for line_break in node.find_all("br"):
        line_break.replace_with("\n")
    value = node.get_text("", strip=False)
    return "\n".join(
        line for raw_line in value.splitlines() if (line := re.sub(r"\s+", " ", raw_line).strip())
    )
