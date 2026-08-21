from importlib import import_module

from report_collector.adapters.base import SourceAdapter
from report_collector.adapters.generic.rendered_board import RenderedBoardAdapter
from report_collector.adapters.generic.rss_feed import RssAdapter
from report_collector.adapters.generic.static_board import StaticBoardAdapter
from report_collector.domain.enums import AdapterKind
from report_collector.domain.models import SourceConfig
from report_collector.providers.browser.base import BrowserRenderer
from report_collector.providers.http.http_client import PublicHttpClient


def build_adapter(
    config: SourceConfig, http: PublicHttpClient, browser: BrowserRenderer | None = None
) -> SourceAdapter:
    if config.implementation:
        module_name, class_name = config.implementation.split(":", 1)
        adapter_class = getattr(import_module(module_name), class_name)
        return adapter_class(config, http, browser)  # type: ignore[no-any-return]
    if config.adapter is AdapterKind.STATIC_BOARD:
        return StaticBoardAdapter(config, http)
    if config.adapter is AdapterKind.RSS:
        return RssAdapter(config, http)
    if config.adapter is AdapterKind.RENDERED_BOARD and browser:
        return RenderedBoardAdapter(config, browser)
    raise ValueError(f"Browser renderer required for {config.id}")
