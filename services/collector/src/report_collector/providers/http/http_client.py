from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx

from .url_policy import ensure_public_url

USER_AGENT = "TodayPublicReportBot/0.1 (+https://localhost/about-collector)"


@dataclass(frozen=True)
class DownloadedFile:
    content: bytes
    content_type: str
    final_url: str


class PublicHttpClient:
    def __init__(self, timeout: float = 20, retries: int = 2, delay_ms: int = 1200) -> None:
        self.timeout = timeout
        self.retries = retries
        self.delay_seconds = delay_ms / 1000

    async def _request_once(self, url: str, max_bytes: int) -> DownloadedFile:
        current = url
        async with httpx.AsyncClient(
            timeout=self.timeout, headers={"user-agent": USER_AGENT}
        ) as client:
            for _ in range(4):
                await ensure_public_url(current)
                async with client.stream("GET", current, follow_redirects=False) as response:
                    if response.is_redirect:
                        current = urljoin(current, response.headers["location"])
                        continue
                    response.raise_for_status()
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > max_bytes:
                            raise ValueError("response exceeds configured size limit")
                    return DownloadedFile(
                        bytes(content), response.headers.get("content-type", ""), str(response.url)
                    )
        raise httpx.TooManyRedirects("redirect limit exceeded", request=httpx.Request("GET", url))

    async def fetch(self, url: str, max_bytes: int = 5_000_000) -> DownloadedFile:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            if attempt:
                await asyncio.sleep(self.delay_seconds * (2 ** (attempt - 1)))
            try:
                result = await self._request_once(url, max_bytes)
                await asyncio.sleep(self.delay_seconds)
                return result
            except (httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout, httpx.RemoteProtocolError) as error:
                last_error = error
                if attempt == self.retries:
                    raise
            except (httpx.HTTPError, OSError) as error:
                last_error = error
                if attempt == self.retries or (isinstance(error, httpx.HTTPStatusError) and error.response.status_code < 500):
                    raise
        assert last_error is not None
        raise last_error

    async def fetch_text(self, url: str) -> str:
        result = await self.fetch(url)
        return _decode_text(result.content, result.content_type)


def _decode_text(content: bytes, content_type: str) -> str:
    """Decode public Korean pages using their declared charset when available."""
    match = re.search(r"charset=([\w-]+)", content_type, flags=re.IGNORECASE)
    encodings = [match.group(1)] if match else []
    encodings.extend(["utf-8", "euc-kr", "cp949"])
    for encoding in dict.fromkeys(encodings):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")
