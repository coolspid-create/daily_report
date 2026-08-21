import time
from typing import Any

import httpx


class TelegramNotificationProvider:
    def __init__(self, token: str, chat_id: str, max_attempts: int = 3) -> None:
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._chat_id = chat_id
        self._max_attempts = max_attempts

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
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = httpx.post(f"{self._base_url}/{method}", json=payload, timeout=20)
                data = response.json()
                if response.is_success and data.get("ok"):
                    return dict(data["result"])
                retry_after = int(data.get("parameters", {}).get("retry_after", 0))
                if response.status_code != 429 and response.status_code < 500:
                    response.raise_for_status()
            except (httpx.HTTPError, ValueError) as error:
                if attempt == self._max_attempts:
                    raise RuntimeError(f"Telegram request failed: {type(error).__name__}") from error
                retry_after = 0
            if attempt < self._max_attempts:
                time.sleep(min(max(retry_after, attempt), 10))
        raise RuntimeError("Telegram request failed after retries")
