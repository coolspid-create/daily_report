import time
from typing import Any

import httpx


class TelegramNotificationProvider:
    def __init__(
        self, token: str, chat_id: str, max_attempts: int = 3, timeout: float = 45.0
    ) -> None:
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._chat_id = chat_id
        self._max_attempts = max_attempts
        self._timeout = timeout

    def send_message(self, html: str) -> str:
        result = self._post(
            "sendMessage",
            {
                "chat_id": self._chat_id,
                "text": html,
                "parse_mode": "HTML",
                "link_preview_options": {"is_disabled": True},
            },
        )
        return str(result["message_id"])

    def send_document(self, document_url: str, caption: str) -> str:
        result = self._post(
            "sendDocument",
            {
                "chat_id": self._chat_id,
                "document": document_url,
                "caption": caption,
            },
        )
        return str(result["message_id"])

    def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = httpx.post(
                    f"{self._base_url}/{method}", json=payload, timeout=self._timeout
                )
                try:
                    data = response.json()
                except Exception:
                    data = {}

                if response.is_success and data.get("ok"):
                    return dict(data["result"])

                # Handle rate limit (429)
                if response.status_code == 429:
                    retry_after = int(data.get("parameters", {}).get("retry_after", 1))
                    if attempt < self._max_attempts:
                        time.sleep(retry_after)
                        continue
                    raise RuntimeError(f"Telegram rate limit exceeded: retry after {retry_after}s")

                # Permanent client error (4xx other than 429) -> Do not retry
                if 400 <= response.status_code < 500:
                    desc = data.get("description") or response.text or f"HTTP {response.status_code}"
                    raise RuntimeError(f"Telegram API client error ({response.status_code}): {desc}")

                # Server error (5xx) -> Retry if attempts remain
                if response.status_code >= 500:
                    last_error = RuntimeError(f"Telegram server error: HTTP {response.status_code}")
                    if attempt < self._max_attempts:
                        time.sleep(attempt * 2)
                        continue
                    raise last_error

                response.raise_for_status()
            except (httpx.ConnectTimeout, httpx.ConnectError, httpx.PoolTimeout) as error:
                last_error = error
                if attempt < self._max_attempts:
                    time.sleep(attempt * 2)
                    continue
                raise RuntimeError(f"Telegram connection failed: {type(error).__name__}") from error
            except httpx.ReadTimeout as error:
                # ReadTimeout means request reached Telegram, do not blind retry to prevent duplicate messages
                raise RuntimeError(
                    f"Telegram response timed out after {self._timeout}s (request may have been processed): {type(error).__name__}"
                ) from error
            except (httpx.HTTPError, ValueError) as error:
                last_error = error
                if attempt == self._max_attempts:
                    raise RuntimeError(f"Telegram request failed: {type(error).__name__}") from error
                time.sleep(attempt)

        assert last_error is not None
        raise RuntimeError(f"Telegram request failed after retries: {last_error}")
