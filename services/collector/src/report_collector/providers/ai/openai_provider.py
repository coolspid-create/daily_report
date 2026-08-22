import json

import httpx
from report_collector.domain.models import AnalysisRequest, AnalysisResult


class OpenAIAnalysisProvider:
    """OpenAI Responses API로 공공 보고서의 구조화된 요약을 생성한다."""

    def __init__(
        self,
        api_key: str,
        model: str,
        endpoint: str = "https://api.openai.com/v1/responses",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.transport = transport

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        async with httpx.AsyncClient(timeout=45, transport=self.transport) as client:
            response = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=self._payload(request),
            )
        response.raise_for_status()
        return AnalysisResult.model_validate_json(_output_text(response.json()))

    def _payload(self, request: AnalysisRequest) -> dict[str, object]:
        return {
            "model": self.model,
            "store": False,
            "instructions": _instructions(),
            "input": _input_text(request),
            "text": {
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": "public_report_analysis",
                    "strict": False,
                    "schema": _response_schema(),
                },
            },
        }


def _instructions() -> str:
    return (
        "당신은 한국 공공 리포트 편집자입니다. 제공한 제목과 원문만 근거로 JSON을 작성하세요. "
        "외부 사실을 추가하거나 추측하지 마세요. why_it_matters에는 독자가 바로 이해할 수 있는 "
        "자연스러운 한국어 2~3문장을 쓰고 240자 이내로 제한하세요. key_points는 핵심 문장 1~3개, "
        "key_tags는 2~8자 한국어 중심 키워드 1~3개로 작성하세요. 원문이 너무 짧거나 의미를 판단할 수 "
        "없으면 summary_kind을 UNAVAILABLE로 하고 그 이유를 why_it_matters에 간결히 쓰세요. 단, "
        "본문이 400자 이상인 일반 문서라면 반드시 ANALYZED로 분석하세요. "
        "페이지 정보가 제공되지 않았다면 evidence_pages는 빈 배열이어야 합니다."
    )


def _input_text(request: AnalysisRequest) -> str:
    page_context = f"PDF 페이지 수: {request.page_count}" if request.page_count else "PDF 페이지 정보 없음"
    return (
        f"제목: {request.title}\n기관: {request.institution}\n{page_context}\n\n"
        f"원문:\n{request.text[:30_000]}"
    )


def _response_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "why_it_matters", "summary_kind", "key_points", "key_tags", "topic_candidates",
            "content_tag", "confidence", "evidence_pages",
        ],
        "properties": {
            "why_it_matters": {"type": "string", "minLength": 1, "maxLength": 240},
            "summary_kind": {"type": "string", "enum": ["ANALYZED", "OFFICIAL_ABSTRACT", "UNAVAILABLE"]},
            "key_points": {
                "type": "array", "minItems": 1, "maxItems": 3,
                "items": {"type": "string", "minLength": 1, "maxLength": 240},
            },
            "key_tags": {
                "type": "array", "minItems": 1, "maxItems": 3,
                "items": {"type": "string", "minLength": 1, "maxLength": 16},
            },
            "topic_candidates": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["economy", "industry", "ai-tech", "labor-welfare", "education-population", "land-environment", "law-security"],
                },
            },
            "content_tag": {"type": "string", "minLength": 1, "maxLength": 40},
            "confidence": {"type": "number"},
            "evidence_pages": {"type": "array", "items": {"type": "integer"}},
        },
    }


def _output_text(payload: dict[str, object]) -> str:
    direct_output = payload.get("output_text")
    if isinstance(direct_output, str):
        return direct_output
    output = payload.get("output")
    if not isinstance(output, list):
        output = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content_items = item.get("content")
        if not isinstance(content_items, list):
            continue
        for content in content_items:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return str(content["text"])
    raise ValueError(f"OpenAI response has no output text: {json.dumps(payload)[:300]}")
