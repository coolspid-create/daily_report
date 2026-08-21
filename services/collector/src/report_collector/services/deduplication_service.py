import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import PurePosixPath
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PREFIX_PATTERN = re.compile(r"^(\[[^\]]+\]|\([^\)]+\)|\d+[.)])\s*")


def normalize_title(title: str) -> str:
    value = unicodedata.normalize("NFKC", title).strip()
    value = PREFIX_PATTERN.sub("", value)
    suffix = PurePosixPath(value).suffix.lower()
    if suffix in {".pdf", ".hwp", ".hwpx", ".doc", ".docx"}:
        value = value[: -len(suffix)]
    value = re.sub(r"[\s\-_·•]+", " ", value)
    return value.casefold().strip()


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    query = urlencode(
        sorted((key, value) for key, value in parse_qsl(parts.query) if not key.startswith("utm_"))
    )
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, "")
    )


@dataclass(frozen=True)
class DuplicateCandidate:
    document_id: str
    detail_url: str
    file_url: str | None
    sha256: str | None
    title: str
    institution: str
    published_at: date | None


def duplicate_reason(candidate: DuplicateCandidate, incoming: DuplicateCandidate) -> str | None:
    if normalize_url(candidate.detail_url) == normalize_url(incoming.detail_url):
        return "URL_EXACT"
    if (
        candidate.file_url
        and incoming.file_url
        and normalize_url(candidate.file_url) == normalize_url(incoming.file_url)
    ):
        return "FILE_URL_EXACT"
    if candidate.sha256 and candidate.sha256 == incoming.sha256:
        return "HASH_EXACT"
    same_context = (
        candidate.published_at == incoming.published_at
        and candidate.institution == incoming.institution
    )
    title_score = SequenceMatcher(
        None, normalize_title(candidate.title), normalize_title(incoming.title)
    ).ratio()
    if same_context and normalize_title(candidate.title) == normalize_title(incoming.title):
        return "TITLE_DATE_INSTITUTION_EXACT"
    if title_score >= 0.9:
        return "TITLE_SIMILAR"
    return None
