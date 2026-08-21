from collections.abc import AsyncIterator
from datetime import UTC, datetime

from report_collector.adapters.base import SourceAdapter
from report_collector.domain.errors import SourceParseError
from report_collector.domain.models import (
    DiscoveredItem,
    SourceConfig,
    SourceDocument,
    SourceHealthResult,
)
from report_collector.providers.http.http_client import PublicHttpClient

LICENSE_ERROR = "미허용 라이센스 사용중"


class KliAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient, *_: object) -> None:
        self.config = config
        self.http = http

    async def discover(self, _: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self.http.fetch_text(str(self.config.list_url))
        if LICENSE_ERROR in html:
            raise SourceParseError("KLI public publication page reports a license error")
        raise SourceParseError("KLI report list structure requires verification")
        yield  # pragma: no cover

    async def fetch_detail(self, _: DiscoveredItem) -> SourceDocument:
        raise SourceParseError("KLI detail fetch is unavailable while the public list is blocked")

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self.http.fetch_text(str(self.config.list_url))
            if LICENSE_ERROR in html:
                return SourceHealthResult(
                    healthy=False, checked_at=datetime.now(UTC), message="public page license error"
                )
            return SourceHealthResult(
                healthy=False,
                checked_at=datetime.now(UTC),
                message="report list parser needs verification",
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )
