from typing import Any

from report_collector.providers.notifications.telegram_provider import (
    TelegramNotificationProvider,
)


class FakeResponse:
    def __init__(self, status_code: int, data: dict[str, Any]) -> None:
        self.status_code = status_code
        self._data = data
        self.is_success = 200 <= status_code < 300

    def json(self) -> dict[str, Any]:
        return self._data

    def raise_for_status(self) -> None:
        raise RuntimeError(f"http {self.status_code}")


def test_telegram_retries_rate_limit(monkeypatch: Any) -> None:
    responses = iter(
        [
            FakeResponse(429, {"ok": False, "parameters": {"retry_after": 1}}),
            FakeResponse(200, {"ok": True, "result": {"message_id": 42}}),
        ]
    )
    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr("time.sleep", lambda _: None)
    provider = TelegramNotificationProvider("secret", "chat", 3)
    assert provider.send_message("briefing") == "42"
