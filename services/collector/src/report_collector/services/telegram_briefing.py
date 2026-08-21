import re
from dataclasses import dataclass
from html import escape
from typing import Any


@dataclass(frozen=True)
class TelegramBriefing:
    messages: tuple[str, ...]
    digest_url: str | None


def build_telegram_briefing(
    snapshot: dict[str, Any], publication_date: str, web_url: str | None = None
) -> TelegramBriefing:
    reports = list(snapshot.get("reportsByTopic", {}).get("all", []))
    header = f"<b>오늘의 공공리포트 · {escape(publication_date)}</b>\n오늘 읽을 자료 {len(reports)}건"
    blocks = [_report_block(index, report) for index, report in enumerate(reports, 1)]
    footer = f'\n<a href="{escape(web_url)}">웹에서 전체 보기</a>' if web_url else ""
    messages = _pack_messages(header, blocks, footer)
    digest = snapshot.get("digests", {}).get("all", {})
    digest_url = str(digest.get("url")) if digest.get("available") and digest.get("url") else None
    return TelegramBriefing(messages, digest_url)


def _report_block(index: int, report: dict[str, Any]) -> str:
    title = escape(str(report.get("title", "제목 없음")))
    date_label = _report_date(report.get("publishedAt"))
    institution = escape(str(report.get("institution", "")))
    tags = " · ".join(escape(str(tag)) for tag in report.get("keyTags", [])[:3])
    file_data = report.get("file", {})
    source_url = escape(str(file_data.get("sourceUrl") or ""))
    download_url = escape(str(file_data.get("downloadUrl") or ""))
    links = []
    if download_url:
        links.append(f'<a href="{download_url}">PDF</a>')
    if source_url:
        links.append(f'<a href="{source_url}">원문</a>')
    meta = " · ".join(part for part in (institution, tags) if part)
    return f"<b>{index}. {title}{date_label}</b>\n{meta}\n{' | '.join(links)}"


def _report_date(value: object) -> str:
    if not isinstance(value, str):
        return ""
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    return f"({match.group(1)}.{match.group(2)}.{match.group(3)})" if match else ""


def _pack_messages(header: str, blocks: list[str], footer: str) -> tuple[str, ...]:
    messages: list[str] = []
    current = header
    for block in blocks:
        candidate = f"{current}\n\n{block}"
        if len(candidate) > 3500 and current != header:
            messages.append(current)
            current = block
        else:
            current = candidate
    messages.append(current + footer)
    return tuple(messages)
