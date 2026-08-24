from typing import Any

import httpx
import pytest
from report_collector.providers.notifications.telegram_provider import (
    TelegramNotificationProvider,
)


class FakeResponse:
    def __init__(self, status_code: int, data: dict[str, Any], text: str = "") -> None:
        self.status_code = status_code
        self._data = data
        self.text = text
        self.is_success = 200 <= status_code < 300

    def json(self) -> dict[str, Any]:
        return self._data

    def raise_for_status(self) -> None:
        if not self.is_success:
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


def test_telegram_does_not_retry_permanent_client_error(monkeypatch: Any) -> None:
    attempts = 0

    def fake_post(*args: Any, **kwargs: Any) -> FakeResponse:
        nonlocal attempts
        attempts += 1
        return FakeResponse(400, {"ok": False, "description": "Bad Request: chat not found"})

    monkeypatch.setattr("httpx.post", fake_post)
    provider = TelegramNotificationProvider("secret", "chat", 3)

    with pytest.raises(RuntimeError, match="Telegram API client error \\(400\\)"):
        provider.send_message("briefing")

    assert attempts == 1


def test_telegram_retries_connect_errors(monkeypatch: Any) -> None:
    attempts = 0

    def fake_post(*args: Any, **kwargs: Any) -> FakeResponse:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise httpx.ConnectError("Network unreachable", request=httpx.Request("POST", "https://api.telegram.org"))
        return FakeResponse(200, {"ok": True, "result": {"message_id": 99}})

    monkeypatch.setattr("httpx.post", fake_post)
    monkeypatch.setattr("time.sleep", lambda _: None)
    provider = TelegramNotificationProvider("secret", "chat", 3)
    assert provider.send_message("briefing") == "99"
    assert attempts == 2


def test_telegram_read_timeout_raises_without_duplicate_retry(monkeypatch: Any) -> None:
    attempts = 0

    def fake_post(*args: Any, **kwargs: Any) -> FakeResponse:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("Response timeout", request=httpx.Request("POST", "https://api.telegram.org"))

    monkeypatch.setattr("httpx.post", fake_post)
    provider = TelegramNotificationProvider("secret", "chat", 3)

    with pytest.raises(RuntimeError, match="Telegram response timed out"):
        provider.send_message("briefing")

    assert attempts == 1
