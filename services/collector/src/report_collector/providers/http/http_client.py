from __future__ import annotations

import asyncio
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
            except (httpx.HTTPError, OSError) as error:
                last_error = error
        assert last_error is not None
        raise last_error

    async def fetch_text(self, url: str) -> str:
        result = await self.fetch(url)
        return result.content.decode("utf-8", errors="replace")
