import asyncio
from urllib.parse import urljoin

from playwright.async_api import Route, async_playwright
from report_collector.providers.http.url_policy import ensure_public_url


class PlaywrightBrowserRenderer:
    def __init__(self, delay_ms: int = 1200) -> None:
        self.delay_seconds = delay_ms / 1000

    async def render(self, url: str, wait_for: str | None, timeout_ms: int) -> str:
        await ensure_public_url(url)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

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
            html = await page.content()
            await browser.close()
            await asyncio.sleep(self.delay_seconds)
            return html

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
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
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
            html = await page.content()
            await browser.close()
            await asyncio.sleep(self.delay_seconds)
            return html
