"""Extract readable main content from official HTML detail pages."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

MAX_OFFICIAL_HTML_CHARS = 3000

CONTENT_SELECTORS = (
    ".p-table__content",
    ".board-view-content",
    ".view-content",
    ".bbs_view_content",
    ".bbs_v_cont",
    ".board_view_con",
    ".board_view",
    ".bbs_view",
    ".content-area",
    ".content_body",
    ".content-body",
    ".article-content",
    ".article-body",
    ".view_cont",
    ".view_txt",
    ".contents_view",
    ".contents",
    ".cont_area",
    ".bd_view",
    "#contents",
    "article",
    "main",
)

NOISE_SELECTOR = (
    "script, style, noscript, nav, header, footer, form, button, aside, "
    ".attachment, .attachments, .attach, .file, .files, .download, .share, "
    ".sns, .pagination"
)


def extract_official_html_content(
    soup: BeautifulSoup | Tag,
    max_length: int = MAX_OFFICIAL_HTML_CHARS,
) -> str | None:
    """Return the meaningful content from a public HTML detail page."""
    for selector in CONTENT_SELECTORS:
        for node in soup.select(selector):
            content = _content_from_node(node)
            if len(content) >= 80:
                return content[:max_length]

    fallback = _paragraph_text(soup)
    return fallback[:max_length] if fallback else None


def _content_from_node(node: Tag) -> str:
    clone = BeautifulSoup(str(node), "html.parser")
    for noise in clone.select(NOISE_SELECTOR):
        noise.decompose()
    return _normalize_text(clone.get_text(" ", strip=True))


def _paragraph_text(soup: BeautifulSoup | Tag) -> str:
    paragraphs = [
        _normalize_text(node.get_text(" ", strip=True))
        for node in soup.select("p, li")
    ]
    return _normalize_text(" ".join(text for text in paragraphs if len(text) >= 20))


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
