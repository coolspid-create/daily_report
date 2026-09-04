import httpx
import pytest
from report_collector.domain.errors import (
    SourceMaintenanceError,
    SourceParseError,
    SourceTimeoutError,
)
from report_collector.pipelines.source_run_guard import classify_error
from report_collector.providers.http.http_client import PublicHttpClient


def test_error_classification_maps_known_exceptions() -> None:
    assert classify_error(SourceTimeoutError("timed out"))[0] == "SOURCE_TIMEOUT"
    assert classify_error(SourceParseError("parse failed"))[0] == "SOURCE_PARSE_ERROR"
    assert classify_error(SourceMaintenanceError("maintenance"))[0] == "SOURCE_MAINTENANCE"

    req = httpx.Request("GET", "https://example.org")
    assert classify_error(httpx.ConnectTimeout("conn timeout", request=req))[0] == "CONNECT_TIMEOUT"
    assert classify_error(httpx.ConnectError("conn failed", request=req))[0] == "CONNECT_ERROR"
    assert classify_error(httpx.ReadTimeout("read timeout", request=req))[0] == "READ_TIMEOUT"

    resp_404 = httpx.Response(404, request=req)
    assert classify_error(httpx.HTTPStatusError("not found", request=req, response=resp_404))[0] == "HTTP_STATUS_404"

    resp_500 = httpx.Response(500, request=req)
    assert classify_error(httpx.HTTPStatusError("server error", request=req, response=resp_500))[0] == "HTTP_STATUS_500"

    assert classify_error(RuntimeError("generic"))[0] == "SOURCE_ERROR"


@pytest.mark.asyncio
async def test_http_client_retries_transient_failures(monkeypatch) -> None:
    attempts = 0

    async def fake_request_once(self, url: str, max_bytes: int):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.ConnectTimeout("Transient connection timeout", request=httpx.Request("GET", url))
        from report_collector.providers.http.http_client import DownloadedFile
        return DownloadedFile(b"<html>Success</html>", "text/html", url)

    monkeypatch.setattr(PublicHttpClient, "_request_once", fake_request_once)

    client = PublicHttpClient(timeout=5, retries=3, delay_ms=0)
    response = await client.fetch("https://example.org/test")
    assert response.content == b"<html>Success</html>"
    assert attempts == 3
