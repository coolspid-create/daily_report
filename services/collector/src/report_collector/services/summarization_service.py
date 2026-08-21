from jsonschema import Draft202012Validator
from report_collector.domain.models import AnalysisRequest, AnalysisResult
from report_collector.providers.ai.base import AnalysisProvider


class SummarizationService:
    def __init__(self, provider: AnalysisProvider, schema: dict[str, object]) -> None:
        self.provider = provider
        self.validator = Draft202012Validator(schema)

    async def summarize(self, request: AnalysisRequest) -> AnalysisResult:
        result = await self.provider.analyze(request)
        self.validator.validate(result.model_dump(mode="json"))
        if request.page_count and any(page > request.page_count for page in result.evidence_pages):
            raise ValueError("evidence page exceeds document page count")
        return result
