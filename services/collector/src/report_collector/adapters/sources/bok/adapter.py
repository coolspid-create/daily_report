import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pydantic import HttpUrl
from report_collector.adapters.generic.rss_feed import RssAdapter
from report_collector.domain.models import Attachment, DiscoveredItem, SourceConfig, SourceDocument
from report_collector.providers.browser.base import BrowserRenderer
from report_collector.providers.http.http_client import PublicHttpClient


class BokRssAdapter(RssAdapter):
    """Read BOK's official RSS summary and public detail-page PDF link."""

    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _browser: BrowserRenderer | None = None
    ) -> None:
        super().__init__(config, http)

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        document = await super().fetch_detail(item)
        html = await self.http.fetch_text(str(item.detail_url))
        attachment = self._pdf_attachment(html, str(item.detail_url))
        attachments = [attachment] if attachment else document.attachments
        return document.model_copy(update={"attachments": attachments})

    @staticmethod
    def _pdf_attachment(html: str, detail_url: str) -> Attachment | None:
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.select("a[href]"):
            href = str(link["href"])
            if not re.search(r"\.pdf(?:[?#]|$)", href, re.IGNORECASE):
                continue
            if "viewer.html" in href:
                continue
            url = urljoin(detail_url, href)
            name = link.get_text(" ", strip=True) or url.rsplit("/", 1)[-1]
            return Attachment(url=HttpUrl(url), file_name=name, declared_type="application/pdf")
        return None
