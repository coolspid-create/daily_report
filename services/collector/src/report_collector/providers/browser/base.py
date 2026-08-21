from typing import Protocol


class BrowserRenderer(Protocol):
    async def render(self, url: str, wait_for: str | None, timeout_ms: int) -> str: ...

    async def submit_form(
        self,
        url: str,
        form_selector: str,
        fields: dict[str, str],
        action: str,
        wait_for: str | None,
        timeout_ms: int,
    ) -> str: ...
