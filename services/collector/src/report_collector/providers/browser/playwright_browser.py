import asyncio
from urllib.parse import urljoin

from playwright.async_api import Browser, BrowserContext, Page, Playwright, Route, async_playwright
from report_collector.providers.http.url_policy import ensure_public_url


class PlaywrightBrowserRenderer:
    def __init__(self, delay_ms: int = 1200) -> None:
        self.delay_seconds = delay_ms / 1000
        self._browser: Browser | None = None
        self._playwright: Playwright | None = None
        self._start_lock = asyncio.Lock()

    async def start(self) -> None:
        if self._browser:
            return
        async with self._start_lock:
            if self._browser:
                return
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _new_page(self) -> tuple[BrowserContext, Page]:
        await self.start()
        if not self._browser:
            raise RuntimeError("Playwright browser did not start")
        context = await self._browser.new_context()
        return context, await context.new_page()

    async def render(self, url: str, wait_for: str | None, timeout_ms: int) -> str:
        await ensure_public_url(url)
        context, page = await self._new_page()
        try:
            async def guard(route: Route) -> None:
                try:
                    await ensure_public_url(route.request.url)
                    await route.continue_()
                except Exception:
                    await route.abort()

            await page.route("**/*", guard)
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=timeout_ms)
            return await page.content()
        finally:
            await context.close()
            await asyncio.sleep(self.delay_seconds)

    async def submit_form(
        self,
        url: str,
        form_selector: str,
        fields: dict[str, str],
        action: str,
        wait_for: str | None,
        timeout_ms: int,
    ) -> str:
        await ensure_public_url(url)
        action_url = urljoin(url, action)
        await ensure_public_url(action_url)
        context, page = await self._new_page()
        try:

            async def guard(route: Route) -> None:
                try:
                    await ensure_public_url(route.request.url)
                    await route.continue_()
                except Exception:
                    await route.abort()

            await page.route("**/*", guard)
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            form = page.locator(form_selector)
            for name, value in fields.items():
                await form.locator(f"[name='{name}']").evaluate(
                    "(node, value) => node.value = value", value
                )
            await form.evaluate("(node, value) => node.action = value", action_url)
            async with page.expect_navigation(wait_until="domcontentloaded", timeout=timeout_ms):
                await form.evaluate("node => node.submit()")
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=timeout_ms)
            return await page.content()
        finally:
            await context.close()
            await asyncio.sleep(self.delay_seconds)
