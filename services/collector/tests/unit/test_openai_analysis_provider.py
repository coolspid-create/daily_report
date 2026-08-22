import json

import httpx
import pytest
from report_collector.domain.models import AnalysisRequest
from report_collector.providers.ai.openai_provider import OpenAIAnalysisProvider


@pytest.mark.asyncio
async def test_openai_provider_requests_structured_analysis() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"output_text": json.dumps(_result())})

    provider = OpenAIAnalysisProvider("test-key", "gpt-test", transport=httpx.MockTransport(handler))
    result = await provider.analyze(_request())
    assert result.why_it_matters.startswith("이 보고서는")
    assert captured["store"] is False
    text = captured["text"]
    assert isinstance(text, dict)
    response_format = text["format"]
    assert isinstance(response_format, dict)
    assert response_format["type"] == "json_schema"


@pytest.mark.asyncio
async def test_openai_provider_reads_responses_content_output() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"output": [{"content": [{"text": json.dumps(_result())}]}]})

    provider = OpenAIAnalysisProvider("test-key", "gpt-test", transport=httpx.MockTransport(handler))
    assert (await provider.analyze(_request())).key_tags == ["푸드테크", "칠레"]


def _request() -> AnalysisRequest:
    return AnalysisRequest(title="칠레 푸드테크 시장", institution="KOTRA", text="공개 본문입니다.")


def _result() -> dict[str, object]:
    return {
        "why_it_matters": "이 보고서는 칠레 푸드테크 시장의 성장 요인을 설명합니다. 현지 협력 기회를 검토하는 데 도움이 됩니다.",
        "summary_kind": "ANALYZED",
        "key_points": ["칠레 푸드테크 시장의 성장 요인을 설명합니다."],
        "key_tags": ["푸드테크", "칠레"],
        "topic_candidates": ["industry"],
        "content_tag": "AI 분석",
        "confidence": 0.9,
        "evidence_pages": [],
    }
